"""Predictive risk analysis service evaluating current telemetry, forecasts, trends, and anomalies."""
import logging
from datetime import datetime, timezone
from typing import List, Optional

import pandas as pd

from app.ml.anomaly_detector import AnomalyDetector
from app.ml.data_processor import DataProcessor
from app.ml.forecaster import ResourceForecaster
from app.schemas.analytics import PredictiveRiskResponse, RiskBreakdown
from app.schemas.metrics import SystemMetricsSnapshot

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """Calculates grounded system operational risk from real-time and predictive indicators."""

    def __init__(
        self,
        data_processor: Optional[DataProcessor] = None,
        forecaster: Optional[ResourceForecaster] = None,
        anomaly_detector: Optional[AnomalyDetector] = None,
    ):
        self.processor = data_processor or DataProcessor()
        self.forecaster = forecaster or ResourceForecaster(data_processor=self.processor)
        self.anomaly_detector = anomaly_detector or AnomalyDetector(data_processor=self.processor)

    def evaluate_risk(
        self,
        current_snapshot: SystemMetricsSnapshot,
        historical_df: Optional[pd.DataFrame] = None,
    ) -> PredictiveRiskResponse:
        """Derive holistic resource risk status from real host telemetry and ML artifacts."""
        now = datetime.now(timezone.utc)
        cpu_val = current_snapshot.cpu.utilization_percent
        mem_val = current_snapshot.memory.utilization_percent
        disk_val = current_snapshot.disk.utilization_percent

        # 1. Evaluate Trends
        cpu_trend_dir = "stable"
        mem_trend_dir = "stable"
        trend_summary_parts = []

        if historical_df is not None and len(historical_df) >= 5:
            featured = self.processor.generate_features(historical_df)
            if not featured.empty and "cpu_trend" in featured.columns:
                latest = featured.iloc[-1]
                c_diff = float(latest["cpu_trend"])
                m_diff = float(latest["memory_trend"])

                if c_diff >= 4.0:
                    cpu_trend_dir = "rising"
                    trend_summary_parts.append(f"CPU climbing (+{round(c_diff, 1)}%)")
                elif c_diff <= -4.0:
                    cpu_trend_dir = "declining"
                    trend_summary_parts.append(f"CPU dropping ({round(c_diff, 1)}%)")
                else:
                    trend_summary_parts.append("CPU stable")

                if m_diff >= 2.0:
                    mem_trend_dir = "rising"
                    trend_summary_parts.append(f"RAM climbing (+{round(m_diff, 1)}%)")
                elif m_diff <= -2.0:
                    mem_trend_dir = "declining"
                    trend_summary_parts.append(f"RAM dropping ({round(m_diff, 1)}%)")
                else:
                    trend_summary_parts.append("RAM stable")
        else:
            trend_summary_parts.append("Telemetry baseline initializing")

        trend_description = ", ".join(trend_summary_parts)

        # 2. Evaluate Forecasted Resource Usage
        forecast_risk = "Normal"
        max_forecasted_util = max(cpu_val, mem_val)

        if historical_df is not None and len(historical_df) >= self.forecaster.min_samples:
            cpu_fc = self.forecaster.forecast_metric(historical_df, metric="cpu")
            mem_fc = self.forecaster.forecast_metric(historical_df, metric="memory")

            for pt in cpu_fc.predictions:
                if pt.predicted_value >= self.anomaly_detector.cpu_critical:
                    forecast_risk = "Critical"
                elif pt.predicted_value >= self.anomaly_detector.cpu_warning and forecast_risk != "Critical":
                    forecast_risk = "High Risk"
                max_forecasted_util = max(max_forecasted_util, pt.predicted_value)

            for pt in mem_fc.predictions:
                if pt.predicted_value >= self.anomaly_detector.memory_critical:
                    forecast_risk = "Critical"
                elif pt.predicted_value >= self.anomaly_detector.memory_warning and forecast_risk != "Critical":
                    forecast_risk = "High Risk"
                max_forecasted_util = max(max_forecasted_util, pt.predicted_value)

        # 3. Detect Anomalies
        anomaly_resp = self.anomaly_detector.detect_all(current_snapshot, historical_df=historical_df)
        active_anomalies = anomaly_resp.anomalies
        has_critical_anomaly = any(a.severity == "Critical" for a in active_anomalies)
        has_high_anomaly = any(a.severity == "High" for a in active_anomalies)

        # 4. Component-specific statuses
        cpu_status = (
            "Critical"
            if cpu_val >= self.anomaly_detector.cpu_critical
            else "High Risk"
            if cpu_val >= self.anomaly_detector.cpu_warning
            else "Warning"
            if cpu_val >= 60.0
            else "Normal"
        )

        mem_status = (
            "Critical"
            if mem_val >= self.anomaly_detector.memory_critical
            else "High Risk"
            if mem_val >= self.anomaly_detector.memory_warning
            else "Warning"
            if mem_val >= 70.0
            else "Normal"
        )

        disk_status = (
            "Critical"
            if disk_val >= self.anomaly_detector.disk_critical
            else "Warning"
            if disk_val >= self.anomaly_detector.disk_warning
            else "Normal"
        )

        network_status = (
            "Warning"
            if max(current_snapshot.network.upload_speed_bps, current_snapshot.network.download_speed_bps)
            >= self.anomaly_detector.net_speed_spike
            else "Normal"
        )

        # 5. Composite Risk Score (0 - 100)
        base_score = (cpu_val * 0.35) + (mem_val * 0.35) + ((max_forecasted_util / 100.0) * 15.0)

        # Trend adjustments
        if cpu_trend_dir == "rising":
            base_score += 5.0
        if mem_trend_dir == "rising":
            base_score += 5.0

        # Anomaly adjustments
        for a in active_anomalies:
            if a.severity == "Critical":
                base_score += 15.0
            elif a.severity == "High":
                base_score += 10.0
            elif a.severity == "Medium":
                base_score += 5.0

        composite_score = round(float(min(100.0, max(0.0, base_score))), 2)

        # 6. Overall Risk Level
        if (
            cpu_status == "Critical"
            or mem_status == "Critical"
            or disk_status == "Critical"
            or forecast_risk == "Critical"
            or has_critical_anomaly
            or composite_score >= 82.0
        ):
            overall_status = "Critical"
        elif (
            cpu_status == "High Risk"
            or mem_status == "High Risk"
            or forecast_risk == "High Risk"
            or has_high_anomaly
            or composite_score >= 65.0
        ):
            overall_status = "High Risk"
        elif (
            cpu_status == "Warning"
            or mem_status == "Warning"
            or disk_status == "Warning"
            or len(active_anomalies) > 0
            or composite_score >= 45.0
        ):
            overall_status = "Warning"
        else:
            overall_status = "Normal"

        # 7. Actionable Recommendations
        recs: List[str] = []
        if cpu_val >= self.anomaly_detector.cpu_warning:
            recs.append("Check high CPU consumers via /api/processes to identify intensive tasks.")
        if mem_val >= self.anomaly_detector.memory_warning:
            recs.append("Memory utilization is high. Free dormant process allocations or add RAM.")
        if disk_val >= self.anomaly_detector.disk_warning:
            recs.append(f"Storage volume {current_snapshot.disk.mount_point} is near capacity. Prune logs and temp files.")
        if forecast_risk in ["High Risk", "Critical"]:
            recs.append(f"Predictive model indicates resource utilization will escalate to {forecast_risk} in the near term.")
        for a in active_anomalies[:2]:
            recs.append(f"[{a.severity} Anomaly] {a.recommended_action}")
        if not recs:
            recs.append("System parameters operate within healthy nominal thresholds.")

        breakdown = RiskBreakdown(
            cpu_status=cpu_status,
            memory_status=mem_status,
            disk_status=disk_status,
            network_status=network_status,
            forecast_risk=forecast_risk,
            trend_description=trend_description,
        )

        return PredictiveRiskResponse(
            timestamp=now,
            risk_status=overall_status,
            risk_score=composite_score,
            current_cpu_percent=round(cpu_val, 2),
            current_memory_percent=round(mem_val, 2),
            recent_cpu_trend=cpu_trend_dir,
            recent_memory_trend=mem_trend_dir,
            breakdown=breakdown,
            active_anomalies_count=len(active_anomalies),
            recommendations=recs,
        )

