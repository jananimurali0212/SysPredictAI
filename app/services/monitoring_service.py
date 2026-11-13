"""Monitoring service coordinating telemetry collection, persistence, and real-time streaming."""
import asyncio
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Optional

from app.collectors.process_collector import ProcessCollector
from app.collectors.system_collector import SystemCollector
from app.config import settings
from app.database.db import Database, get_db
from app.ml.anomaly_detector import AnomalyDetector
from app.ml.data_processor import DataProcessor
from app.ml.forecaster import ResourceForecaster
from app.ml.risk_analyzer import RiskAnalyzer
from app.schemas.analytics import (
    AnomalyDetectionResponse,
    PredictiveRiskResponse,
    PredictionResponse,
    PredictionSummary,
)
from app.schemas.metrics import (
    HealthResponse,
    HistoricalMetricsResponse,
    ProcessListResponse,
    SystemInfo,
    SystemMetricsSnapshot,
)
from app.websocket.manager import ConnectionManager, get_connection_manager

logger = logging.getLogger(__name__)


class MonitoringService:
    """Core orchestrator for system metric collection, persistence, and real-time streaming."""

    def __init__(
        self,
        system_collector: Optional[SystemCollector] = None,
        process_collector: Optional[ProcessCollector] = None,
        database: Optional[Database] = None,
        connection_manager: Optional[ConnectionManager] = None,
        data_processor: Optional[DataProcessor] = None,
        forecaster: Optional[ResourceForecaster] = None,
        anomaly_detector: Optional[AnomalyDetector] = None,
        risk_analyzer: Optional[RiskAnalyzer] = None,
    ):
        self.system_collector = system_collector or SystemCollector()
        self.process_collector = process_collector or ProcessCollector()
        self.db = database or get_db()
        self.ws_manager = connection_manager or get_connection_manager()

        # ML & Predictive Analytics Services
        self.data_processor = data_processor or DataProcessor(database=self.db)
        self.forecaster = forecaster or ResourceForecaster(data_processor=self.data_processor)
        self.anomaly_detector = anomaly_detector or AnomalyDetector(data_processor=self.data_processor)
        self.risk_analyzer = risk_analyzer or RiskAnalyzer(
            data_processor=self.data_processor,
            forecaster=self.forecaster,
            anomaly_detector=self.anomaly_detector,
        )

        self._start_time: float = time.time()
        self._latest_snapshot: Optional[SystemMetricsSnapshot] = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._cleanup_counter: int = 0

    async def start(self) -> None:
        """Start the background metrics collection thread and initialize state."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return

            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = None

            self._stop_event.clear()

            # Immediate warm-up collection to populate cache and database
            try:
                snapshot = self.system_collector.collect_all()
                record_id = self.db.save_metric(snapshot)
                snapshot.id = record_id
                self._latest_snapshot = snapshot
            except Exception as e:
                logger.error("Initial metrics warm-up encountered an error: %s", e)

            # Start background collection in a dedicated daemon thread
            self._thread = threading.Thread(
                target=self._worker_loop,
                name="SystemMonitoringWorker",
                daemon=True,
            )
            self._thread.start()
            logger.info("System monitoring background worker started.")

    async def stop(self) -> None:
        """Signal background worker to stop and wait for completion."""
        with self._lock:
            if self._thread is None:
                return

            self._stop_event.set()
            thread = self._thread
            self._thread = None

        if thread and thread.is_alive():
            thread.join(timeout=2.0)
            logger.info("System monitoring background worker stopped.")

    def _worker_loop(self) -> None:
        """Dedicated background worker collecting, saving, and broadcasting metrics."""
        while not self._stop_event.is_set():
            try:
                start_ts = time.time()

                # Collect metrics from host
                snapshot = self.system_collector.collect_all()

                # Persist to SQLite
                record_id = self.db.save_metric(snapshot)
                snapshot.id = record_id

                with self._lock:
                    self._latest_snapshot = snapshot

                # Broadcast to active WebSocket connections
                if self.ws_manager.client_count > 0 and self._loop and self._loop.is_running():
                    try:
                        payload = snapshot.model_dump(mode="json")
                        asyncio.run_coroutine_threadsafe(
                            self.ws_manager.broadcast_json(payload),
                            self._loop,
                        )
                    except Exception as b_err:
                        logger.debug("Failed to dispatch broadcast to event loop: %s", b_err)

                # Periodic history pruning (roughly once per hour)
                self._cleanup_counter += 1
                if self._cleanup_counter >= 3600:
                    self._cleanup_counter = 0
                    try:
                        self.db.cleanup_old_metrics(settings.HISTORY_RETENTION_HOURS)
                    except Exception as c_err:
                        logger.warning("Error pruning historical metrics: %s", c_err)

                # Wait for next interval or stop signal
                elapsed = time.time() - start_ts
                sleep_sec = max(0.05, settings.METRICS_INTERVAL_SECONDS - elapsed)
                if self._stop_event.wait(timeout=sleep_sec):
                    break

            except Exception as e:
                logger.error("Error in system monitoring worker loop: %s", e, exc_info=True)
                if self._stop_event.wait(timeout=1.0):
                    break

    def get_current_metrics(self) -> SystemMetricsSnapshot:
        """Return the most recently collected system metrics snapshot."""
        with self._lock:
            if self._latest_snapshot is not None:
                return self._latest_snapshot

        # Fallback if no snapshot cached yet
        snapshot = self.system_collector.collect_all()
        with self._lock:
            self._latest_snapshot = snapshot
        return snapshot

    def get_history(
        self,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> HistoricalMetricsResponse:
        """Fetch historical system telemetry from SQLite."""
        snapshots = self.db.get_history(limit=limit, start_time=start_time, end_time=end_time)
        return HistoricalMetricsResponse(
            count=len(snapshots),
            metrics=snapshots,
        )

    def get_processes(self, limit: int = 50, sort_by: str = "cpu") -> ProcessListResponse:
        """Fetch active process metrics sorted by CPU or memory consumption."""
        procs = self.process_collector.collect_processes(limit=limit, sort_by=sort_by)
        return ProcessListResponse(
            count=len(procs),
            processes=procs,
        )

    def get_system_info(self) -> SystemInfo:
        """Retrieve host system information and hardware specifications."""
        return self.system_collector.get_system_info()

    def get_health(self) -> HealthResponse:
        """Verify service components and return health status."""
        uptime = max(0.0, time.time() - self._start_time)
        db_healthy = self.db.is_healthy()

        collectors_healthy = False
        try:
            sample_cpu = self.system_collector.collect_cpu()
            collectors_healthy = sample_cpu.core_count_logical > 0
        except Exception:
            collectors_healthy = False

        status = "healthy" if (db_healthy and collectors_healthy) else "degraded"

        return HealthResponse(
            status=status,
            timestamp=datetime.now(timezone.utc),
            version=settings.APP_VERSION,
            uptime_seconds=round(uptime, 2),
            collectors_healthy=collectors_healthy,
            database_healthy=db_healthy,
        )

    def get_cpu_prediction(self, horizons_seconds: Optional[list] = None) -> PredictionResponse:
        """Fetch historical records from DB and generate short-term CPU utilization forecast."""
        df = self.db.get_history_df(limit=2000)
        return self.forecaster.forecast_metric(df, metric="cpu", horizons_seconds=horizons_seconds)

    def get_memory_prediction(self, horizons_seconds: Optional[list] = None) -> PredictionResponse:
        """Fetch historical records from DB and generate short-term RAM utilization forecast."""
        df = self.db.get_history_df(limit=2000)
        return self.forecaster.forecast_metric(df, metric="memory", horizons_seconds=horizons_seconds)

    def get_prediction_summary(self) -> PredictionSummary:
        """Synthesize CPU and Memory forecasts into an executive prediction summary."""
        df = self.db.get_history_df(limit=2000)
        return self.forecaster.forecast_summary(df)

    def get_anomalies(self) -> AnomalyDetectionResponse:
        """Detect current system anomalies using rule thresholds and Isolation Forest."""
        current_snapshot = self.get_current_metrics()
        df = self.db.get_history_df(limit=500)
        return self.anomaly_detector.detect_all(current_snapshot, historical_df=df)

    def get_risk_assessment(self) -> PredictiveRiskResponse:
        """Evaluate multi-factor operational risk across current metrics, trends, forecasts, and anomalies."""
        current_snapshot = self.get_current_metrics()
        df = self.db.get_history_df(limit=500)
        return self.risk_analyzer.evaluate_risk(current_snapshot, historical_df=df)


_service_instance: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Retrieve or initialize the singleton MonitoringService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = MonitoringService()
    return _service_instance
