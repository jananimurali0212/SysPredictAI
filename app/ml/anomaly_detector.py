"""System anomaly detection module combining rule-based heuristics and Isolation Forest ML."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from app.config import settings
from app.ml.data_processor import DataProcessor
from app.schemas.analytics import AnomalyDetectionResponse, AnomalyItem
from app.schemas.metrics import SystemMetricsSnapshot

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detects metric spikes, threshold breaches, and multivariate anomalies."""

    def __init__(
        self,
        data_processor: Optional[DataProcessor] = None,
        cpu_warning: Optional[float] = None,
        cpu_critical: Optional[float] = None,
        memory_warning: Optional[float] = None,
        memory_critical: Optional[float] = None,
        disk_warning: Optional[float] = None,
        disk_critical: Optional[float] = None,
        net_speed_spike: Optional[float] = None,
        iso_contamination: Optional[float] = None,
        iso_min_samples: Optional[int] = None,
    ):
        self.processor = data_processor or DataProcessor()
        self.cpu_warning = cpu_warning or settings.ANOMALY_CPU_WARNING
        self.cpu_critical = cpu_critical or settings.ANOMALY_CPU_CRITICAL
        self.memory_warning = memory_warning or settings.ANOMALY_MEMORY_WARNING
        self.memory_critical = memory_critical or settings.ANOMALY_MEMORY_CRITICAL
        self.disk_warning = disk_warning or settings.ANOMALY_DISK_WARNING
        self.disk_critical = disk_critical or settings.ANOMALY_DISK_CRITICAL
        self.net_speed_spike = net_speed_spike or settings.ANOMALY_NET_SPEED_SPIKE_BPS
        self.iso_contamination = iso_contamination or settings.ISOLATION_FOREST_CONTAMINATION
        self.iso_min_samples = iso_min_samples or settings.ISOLATION_FOREST_MIN_SAMPLES

        self._iso_forest: Optional[IsolationForest] = None
        self._fitted_samples_count: int = 0

    def check_rules(
        self,
        snapshot: SystemMetricsSnapshot,
        recent_history: Optional[pd.DataFrame] = None,
    ) -> List[AnomalyItem]:
        """Perform rule-based anomaly detection against single snapshot and recent history."""
        anomalies: List[AnomalyItem] = []
        ts = snapshot.timestamp

        # 1. CPU Rules
        cpu_val = snapshot.cpu.utilization_percent
        if cpu_val >= self.cpu_critical:
            anomalies.append(
                AnomalyItem(
                    anomaly_id=f"anom_cpu_crit_{int(ts.timestamp())}",
                    timestamp=ts,
                    metric_name="cpu",
                    observed_value=cpu_val,
                    threshold_or_baseline=self.cpu_critical,
                    anomaly_score=1.0,
                    detection_method="rule_based",
                    severity="Critical",
                    explanation=f"CPU utilization ({cpu_val}%) reached critical threshold ({self.cpu_critical}%).",
                    recommended_action="Inspect high-CPU processes via /api/processes and terminate or throttle non-essential workloads.",
                )
            )
        elif cpu_val >= self.cpu_warning:
            anomalies.append(
                AnomalyItem(
                    anomaly_id=f"anom_cpu_warn_{int(ts.timestamp())}",
                    timestamp=ts,
                    metric_name="cpu",
                    observed_value=cpu_val,
                    threshold_or_baseline=self.cpu_warning,
                    anomaly_score=0.7,
                    detection_method="rule_based",
                    severity="High",
                    explanation=f"CPU utilization ({cpu_val}%) exceeded warning threshold ({self.cpu_warning}%).",
                    recommended_action="Monitor ongoing tasks for sustained load and prepare workload distribution.",
                )
            )

        # CPU Sudden Spike detection (compared to rolling average if available)
        if recent_history is not None and len(recent_history) >= 10:
            past_cpu = recent_history["cpu_percent"].iloc[-10:-1]
            mean_past_cpu = float(past_cpu.mean())
            if (cpu_val - mean_past_cpu) >= 35.0 and cpu_val < self.cpu_warning:
                anomalies.append(
                    AnomalyItem(
                        anomaly_id=f"anom_cpu_spike_{int(ts.timestamp())}",
                        timestamp=ts,
                        metric_name="cpu",
                        observed_value=cpu_val,
                        threshold_or_baseline=round(mean_past_cpu, 2),
                        anomaly_score=0.6,
                        detection_method="rule_based",
                        severity="Medium",
                        explanation=f"Rapid CPU surge: jumped +{round(cpu_val - mean_past_cpu, 1)}% above recent 10-sample baseline ({round(mean_past_cpu, 1)}%).",
                        recommended_action="Check for recently initiated cron jobs, compiler runs, or bursty background tasks.",
                    )
                )

        # 2. RAM Rules
        mem_val = snapshot.memory.utilization_percent
        if mem_val >= self.memory_critical:
            anomalies.append(
                AnomalyItem(
                    anomaly_id=f"anom_mem_crit_{int(ts.timestamp())}",
                    timestamp=ts,
                    metric_name="memory",
                    observed_value=mem_val,
                    threshold_or_baseline=self.memory_critical,
                    anomaly_score=1.0,
                    detection_method="rule_based",
                    severity="Critical",
                    explanation=f"RAM utilization ({mem_val}%) reached critical threshold ({self.memory_critical}%). System at risk of OOM.",
                    recommended_action="Identify memory-leaking processes using /api/processes and free buffer caches.",
                )
            )
        elif mem_val >= self.memory_warning:
            anomalies.append(
                AnomalyItem(
                    anomaly_id=f"anom_mem_warn_{int(ts.timestamp())}",
                    timestamp=ts,
                    metric_name="memory",
                    observed_value=mem_val,
                    threshold_or_baseline=self.memory_warning,
                    anomaly_score=0.7,
                    detection_method="rule_based",
                    severity="Medium",
                    explanation=f"RAM utilization ({mem_val}%) exceeded warning threshold ({self.memory_warning}%).",
                    recommended_action="Review high memory footprint processes.",
                )
            )

        # 3. Disk Rules
        disk_val = snapshot.disk.utilization_percent
        if disk_val >= self.disk_critical:
            anomalies.append(
                AnomalyItem(
                    anomaly_id=f"anom_disk_crit_{int(ts.timestamp())}",
                    timestamp=ts,
                    metric_name="disk",
                    observed_value=disk_val,
                    threshold_or_baseline=self.disk_critical,
                    anomaly_score=0.95,
                    detection_method="rule_based",
                    severity="Critical",
                    explanation=f"Storage volume ({snapshot.disk.mount_point}) reached {disk_val}% capacity.",
                    recommended_action="Prune old log files, temp files, and clear caches to prevent disk exhaustion.",
                )
            )
        elif disk_val >= self.disk_warning:
            anomalies.append(
                AnomalyItem(
                    anomaly_id=f"anom_disk_warn_{int(ts.timestamp())}",
                    timestamp=ts,
                    metric_name="disk",
                    observed_value=disk_val,
                    threshold_or_baseline=self.disk_warning,
                    anomaly_score=0.6,
                    detection_method="rule_based",
                    severity="Low",
                    explanation=f"Storage volume ({snapshot.disk.mount_point}) at {disk_val}% capacity.",
                    recommended_action="Schedule routine cleanup of temporary directories.",
                )
            )

        # 4. Network Rules
        net_max_speed = max(snapshot.network.upload_speed_bps, snapshot.network.download_speed_bps)
        if net_max_speed >= self.net_speed_spike:
            spike_type = "Upload" if snapshot.network.upload_speed_bps >= snapshot.network.download_speed_bps else "Download"
            speed_mb = round(net_max_speed / (1024 * 1024), 2)
            anomalies.append(
                AnomalyItem(
                    anomaly_id=f"anom_net_spike_{int(ts.timestamp())}",
                    timestamp=ts,
                    metric_name="network",
                    observed_value=round(net_max_speed, 2),
                    threshold_or_baseline=self.net_speed_spike,
                    anomaly_score=0.8,
                    detection_method="rule_based",
                    severity="Medium",
                    explanation=f"Abnormally high network {spike_type} activity detected: {speed_mb} MB/s.",
                    recommended_action="Investigate heavy network transfer connections and active download/upload sessions.",
                )
            )

        return anomalies

    def check_isolation_forest(
        self,
        historical_df: pd.DataFrame,
    ) -> List[AnomalyItem]:
        """Run Isolation Forest anomaly detection across multidimensional telemetry features."""
        if historical_df.empty or len(historical_df) < self.iso_min_samples:
            return []

        cleaned = self.processor.clean_and_sort(historical_df)
        if len(cleaned) < self.iso_min_samples:
            return []

        feature_cols = [
            "cpu_percent",
            "memory_percent",
            "disk_percent",
            "upload_speed_bps",
            "download_speed_bps",
        ]
        available_cols = [c for c in feature_cols if c in cleaned.columns]
        if len(available_cols) < 3:
            return []

        X = cleaned[available_cols].values

        # Fit Isolation Forest
        iso = IsolationForest(
            contamination=self.iso_contamination,
            random_state=42,
            n_estimators=100,
            n_jobs=1,
        )
        iso.fit(X)
        self._iso_forest = iso
        self._fitted_samples_count = len(X)

        # Evaluate the most recent observation(s) - last 1 to 3 records
        decision_scores = iso.decision_function(X)
        predictions = iso.predict(X)  # -1 for anomaly, 1 for normal

        anomalies: List[AnomalyItem] = []
        # Inspect the latest sample
        latest_idx = len(X) - 1
        if predictions[latest_idx] == -1:
            raw_score = decision_scores[latest_idx]
            # Convert raw score to positive anomaly magnitude (more negative = more anomalous)
            anomaly_magnitude = round(float(np.clip(-raw_score * 2.0, 0.1, 1.0)), 2)
            latest_row = cleaned.iloc[latest_idx]
            ts = latest_row["timestamp"]
            if not isinstance(ts, datetime):
                ts = pd.to_datetime(ts, utc=True).to_pydatetime()

            # Determine dominant contributing metric
            col_means = cleaned[available_cols].mean()
            col_stds = cleaned[available_cols].std().replace(0, 1.0)
            z_scores = np.abs((latest_row[available_cols] - col_means) / col_stds)
            lead_metric = str(z_scores.idxmax()).replace("_percent", "").replace("_bps", "")

            severity = "High" if anomaly_magnitude >= 0.7 else "Medium"

            anomalies.append(
                AnomalyItem(
                    anomaly_id=f"anom_iso_{int(ts.timestamp())}_{uuid.uuid4().hex[:6]}",
                    timestamp=ts,
                    metric_name=lead_metric,
                    observed_value=round(float(latest_row.get(f"{lead_metric}_percent", latest_row.get(f"{lead_metric}_speed_bps", 0.0))), 2),
                    threshold_or_baseline=round(float(col_means.get(f"{lead_metric}_percent", col_means.get(f"{lead_metric}_speed_bps", 0.0))), 2),
                    anomaly_score=anomaly_magnitude,
                    detection_method="isolation_forest",
                    severity=severity,
                    explanation=f"Multivariate outlier pattern detected by Isolation Forest (score: {anomaly_magnitude}). Primary deviation on {lead_metric}.",
                    recommended_action="Audit correlation between system background threads, I/O bursts, and process memory churn.",
                )
            )

        return anomalies

    def detect_all(
        self,
        current_snapshot: SystemMetricsSnapshot,
        historical_df: Optional[pd.DataFrame] = None,
    ) -> AnomalyDetectionResponse:
        """Combine rule-based threshold detection and ML Isolation Forest into structured response."""
        now = datetime.now(timezone.utc)
        rule_anomalies = self.check_rules(current_snapshot, recent_history=historical_df)

        iso_anomalies: List[AnomalyItem] = []
        iso_enabled = False

        if historical_df is not None and len(historical_df) >= self.iso_min_samples:
            iso_anomalies = self.check_isolation_forest(historical_df)
            iso_enabled = True

        all_anomalies = rule_anomalies + iso_anomalies

        # Sort anomalies: Critical > High > Medium > Low
        severity_rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        all_anomalies.sort(key=lambda a: severity_rank.get(a.severity, 4))

        return AnomalyDetectionResponse(
            timestamp=now,
            total_anomalies=len(all_anomalies),
            isolation_forest_enabled=iso_enabled,
            anomalies=all_anomalies,
        )
