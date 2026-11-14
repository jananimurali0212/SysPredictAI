"""FastAPI route handlers for telemetry REST endpoints and WebSocket stream."""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.schemas.ai import (
    AIInsightQueryRequest,
    AIInsightResponse,
    AISummaryResponse,
)
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
from app.services.ai_service import AIService, get_ai_service
from app.services.monitoring_service import MonitoringService, get_monitoring_service
from app.websocket.manager import ConnectionManager, get_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Monitoring"])
ws_router = APIRouter(tags=["WebSocket"])


@router.get("/health", response_model=HealthResponse, summary="Service health status")
async def health_check(
    service: MonitoringService = Depends(get_monitoring_service),
) -> HealthResponse:
    """Check availability of system collectors and SQLite database."""
    return service.get_health()


@router.get("/metrics/current", response_model=SystemMetricsSnapshot, summary="Current system metrics")
async def get_current_metrics(
    service: MonitoringService = Depends(get_monitoring_service),
) -> SystemMetricsSnapshot:
    """Get the latest real hardware metrics for CPU, RAM, Disk, and Network."""
    return service.get_current_metrics()


@router.get("/metrics/history", response_model=HistoricalMetricsResponse, summary="Historical metrics")
async def get_metrics_history(
    limit: int = Query(default=100, ge=1, le=1000, description="Max snapshots to retrieve"),
    start_time: Optional[datetime] = Query(default=None, description="Filter records starting from UTC timestamp"),
    end_time: Optional[datetime] = Query(default=None, description="Filter records up to UTC timestamp"),
    service: MonitoringService = Depends(get_monitoring_service),
) -> HistoricalMetricsResponse:
    """Query persisted historical system metric snapshots."""
    return service.get_history(limit=limit, start_time=start_time, end_time=end_time)


@router.get("/processes", response_model=ProcessListResponse, summary="Active process table")
async def get_processes(
    limit: int = Query(default=50, ge=1, le=500, description="Maximum number of processes to return"),
    sort_by: str = Query(default="cpu", pattern="^(cpu|memory)$", description="Sort attribute ('cpu' or 'memory')"),
    service: MonitoringService = Depends(get_monitoring_service),
) -> ProcessListResponse:
    """List running processes with CPU and memory usage, handling access-denied safely."""
    return service.get_processes(limit=limit, sort_by=sort_by)


@router.get("/system/info", response_model=SystemInfo, summary="Host machine specifications")
async def get_system_info(
    service: MonitoringService = Depends(get_monitoring_service),
) -> SystemInfo:
    """Retrieve host machine platform, CPU cores, memory size, and boot time."""
    return service.get_system_info()


# ============================================================================
# Day 2: Predictive Analytics & Anomaly Detection Endpoints
# ============================================================================


@router.get(
    "/predictions/cpu",
    response_model=PredictionResponse,
    tags=["Predictive Analytics"],
    summary="CPU utilization forecast",
)
async def predict_cpu_utilization(
    horizons: Optional[str] = Query(
        default=None,
        description="Comma-separated future prediction intervals in seconds (e.g. '60,300,900')",
    ),
    service: MonitoringService = Depends(get_monitoring_service),
) -> PredictionResponse:
    """Forecast future short-term CPU utilization using Random Forest trained on real historical metrics."""
    parsed_horizons = None
    if horizons:
        try:
            parsed_horizons = [int(h.strip()) for h in horizons.split(",") if h.strip()]
        except ValueError:
            parsed_horizons = None
    return service.get_cpu_prediction(horizons_seconds=parsed_horizons)


@router.get(
    "/predictions/memory",
    response_model=PredictionResponse,
    tags=["Predictive Analytics"],
    summary="RAM utilization forecast",
)
async def predict_memory_utilization(
    horizons: Optional[str] = Query(
        default=None,
        description="Comma-separated future prediction intervals in seconds (e.g. '60,300,900')",
    ),
    service: MonitoringService = Depends(get_monitoring_service),
) -> PredictionResponse:
    """Forecast future short-term Memory utilization using Random Forest trained on real historical metrics."""
    parsed_horizons = None
    if horizons:
        try:
            parsed_horizons = [int(h.strip()) for h in horizons.split(",") if h.strip()]
        except ValueError:
            parsed_horizons = None
    return service.get_memory_prediction(horizons_seconds=parsed_horizons)


@router.get(
    "/predictions/summary",
    response_model=PredictionSummary,
    tags=["Predictive Analytics"],
    summary="Executive resource forecast summary",
)
async def get_predictions_summary(
    service: MonitoringService = Depends(get_monitoring_service),
) -> PredictionSummary:
    """Aggregated predictive resource forecast covering CPU and Memory."""
    return service.get_prediction_summary()


@router.get(
    "/anomalies",
    response_model=AnomalyDetectionResponse,
    tags=["Anomaly Detection"],
    summary="System anomaly detection",
)
async def get_anomalies(
    service: MonitoringService = Depends(get_monitoring_service),
) -> AnomalyDetectionResponse:
    """Detect current anomalies using rule-based threshold filters and scikit-learn Isolation Forest."""
    return service.get_anomalies()


@router.get(
    "/risk",
    response_model=PredictiveRiskResponse,
    tags=["Risk Assessment"],
    summary="Holistic predictive risk status",
)
async def get_system_risk(
    service: MonitoringService = Depends(get_monitoring_service),
) -> PredictiveRiskResponse:
    """Evaluate comprehensive operational risk from current metrics, trends, forecasts, and anomalies."""
    return service.get_risk_assessment()


# ============================================================================
# Day 3: Gemini-Powered AI Insights & System Diagnostics Endpoints
# ============================================================================


@router.post(
    "/insights/query",
    response_model=AIInsightResponse,
    tags=["AI Insights"],
    summary="Ask Gemini AI about system performance",
)
async def query_ai_insights(
    payload: AIInsightQueryRequest,
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    ai_service: AIService = Depends(get_ai_service),
) -> AIInsightResponse:
    """Analyze host telemetry and answer user questions using Gemini or telemetry heuristics."""
    current_metrics = monitoring_service.get_current_metrics()
    procs = monitoring_service.get_processes(limit=6, sort_by="cpu").processes
    anoms = monitoring_service.get_anomalies().anomalies
    risk_resp = monitoring_service.get_risk_assessment()
    cpu_pred = monitoring_service.get_cpu_prediction(horizons_seconds=[60])
    return await ai_service.answer_question(
        question=payload.question,
        current_metrics=current_metrics,
        top_processes=procs,
        anomalies=anoms,
        risk_resp=risk_resp,
        cpu_prediction=cpu_pred,
    )


@router.get(
    "/insights/summary",
    response_model=AISummaryResponse,
    tags=["AI Insights"],
    summary="Executive AI system health summary",
)
async def get_ai_summary(
    monitoring_service: MonitoringService = Depends(get_monitoring_service),
    ai_service: AIService = Depends(get_ai_service),
) -> AISummaryResponse:
    """Generate high-level synthesized system status statement for the Overview dashboard."""
    current_metrics = monitoring_service.get_current_metrics()
    anoms = monitoring_service.get_anomalies().anomalies
    risk_resp = monitoring_service.get_risk_assessment()
    return ai_service.generate_system_summary(
        current_metrics=current_metrics,
        anomalies=anoms,
        risk_resp=risk_resp,
    )


@ws_router.websocket("/ws/metrics")
async def websocket_metrics_stream(
    websocket: WebSocket,
    service: MonitoringService = Depends(get_monitoring_service),
    manager: ConnectionManager = Depends(get_connection_manager),
):
    """Real-time WebSocket stream delivering updated system metrics at 1-second cadence."""
    await manager.connect(websocket)

    # Immediately push the latest current metrics snapshot on connect
    try:
        current_snapshot = service.get_current_metrics()
        await websocket.send_json(current_snapshot.model_dump(mode="json"))
    except Exception as e:
        logger.debug("Failed to deliver initial snapshot to WebSocket client: %s", e)

    try:
        # Keep connection open and handle optional client pings
        while True:
            # Client messages (such as ping/pong or settings)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                # Echo or handle client heartbeat if needed
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Idle timeout keepalive: verify socket is still healthy
                continue
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.warning("WebSocket stream encountered error: %s", e)
        await manager.disconnect(websocket)

