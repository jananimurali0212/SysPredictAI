"""Automated tests for machine learning resource forecasting, anomaly detection, and predictive risk analysis."""
import os
import tempfile
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd
import pytest

from app.database.db import Database
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
    CPUMetrics,
    DiskMetrics,
    MemoryMetrics,
    NetworkMetrics,
    SystemMetricsSnapshot,
)


def create_synthetic_snapshot(
    ts: datetime,
    cpu: float = 25.0,
    mem: float = 40.0,
    disk: float = 50.0,
    upload: float = 1000.0,
    download: float = 2000.0,
) -> SystemMetricsSnapshot:
    """Helper to build a controlled test snapshot."""
    return SystemMetricsSnapshot(
        timestamp=ts,
        cpu=CPUMetrics(
            utilization_percent=cpu,
            per_core_utilization=[cpu, cpu],
            core_count_physical=2,
            core_count_logical=2,
            frequency=None,
        ),
        memory=MemoryMetrics(
            total_bytes=16000000000,
            used_bytes=int(16000000000 * (mem / 100.0)),
            available_bytes=int(16000000000 * ((100.0 - mem) / 100.0)),
            utilization_percent=mem,
        ),
        disk=DiskMetrics(
            mount_point="C:\\",
            total_bytes=500000000000,
            used_bytes=int(500000000000 * (disk / 100.0)),
            available_bytes=int(500000000000 * ((100.0 - disk) / 100.0)),
            utilization_percent=disk,
        ),
        network=NetworkMetrics(
            bytes_sent=100000,
            bytes_recv=200000,
            upload_speed_bps=upload,
            download_speed_bps=download,
        ),
    )


def generate_synthetic_dataframe(n_samples: int = 60, base_cpu: float = 30.0, base_mem: float = 45.0) -> pd.DataFrame:
    """Generate controlled time-series dataframe for testing."""
    start_time = datetime(2026, 11, 13, 10, 0, 0, tzinfo=timezone.utc)
    records = []
    for i in range(n_samples):
        ts = start_time + timedelta(seconds=i * 2)
        # Smooth cyclic pattern with slight trend
        cpu = np.clip(base_cpu + 5.0 * np.sin(i / 5.0) + (i * 0.1), 0.0, 100.0)
        mem = np.clip(base_mem + 3.0 * np.cos(i / 7.0) + (i * 0.05), 0.0, 100.0)
        records.append(
            {
                "id": i + 1,
                "timestamp": ts.isoformat(),
                "cpu_percent": round(float(cpu), 2),
                "cpu_cores_logical": 4,
                "memory_percent": round(float(mem), 2),
                "memory_used_bytes": int(16000000000 * (mem / 100.0)),
                "memory_total_bytes": 16000000000,
                "disk_percent": 55.0,
                "disk_used_bytes": 275000000000,
                "disk_total_bytes": 500000000000,
                "bytes_sent": 1000000 + (i * 5000),
                "bytes_recv": 2000000 + (i * 10000),
                "upload_speed_bps": 5000.0,
                "download_speed_bps": 10000.0,
            }
        )
    return pd.DataFrame(records)


# ============================================================================
# 1. Historical Data Retrieval Test
# ============================================================================


def test_historical_data_retrieval():
    """Verify that DataProcessor retrieves and formats records from the SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db = Database(db_path=db_path)
        db.init_db()

        # Seed database with controlled test snapshots
        base_time = datetime(2026, 11, 13, 12, 0, 0, tzinfo=timezone.utc)
        for i in range(5):
            snap = create_synthetic_snapshot(base_time + timedelta(seconds=i), cpu=20.0 + i)
            db.save_metric(snap)

        processor = DataProcessor(database=db)
        raw_df = processor.fetch_historical_dataframe(limit=10)

        assert not raw_df.empty
        assert len(raw_df) == 5
        assert "cpu_percent" in raw_df.columns
        assert "memory_percent" in raw_df.columns
        assert "timestamp" in raw_df.columns

        # Verify cleaning and chronological sorting
        clean_df = processor.clean_and_sort(raw_df)
        assert len(clean_df) == 5
        # Verify timestamps are strictly ascending
        for i in range(len(clean_df) - 1):
            assert clean_df["timestamp"].iloc[i] <= clean_df["timestamp"].iloc[i + 1]

    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass


# ============================================================================
# 2. Feature Generation Test
# ============================================================================


def test_feature_generation():
    """Verify lag, rolling average, volatility, and trend features are generated correctly."""
    df = generate_synthetic_dataframe(n_samples=40)
    processor = DataProcessor()
    featured = processor.generate_features(df)

    assert not featured.empty
    assert len(featured) == 40

    # Verify lag features exist
    for lag in [1, 2, 3, 5]:
        assert f"cpu_lag_{lag}" in featured.columns
        assert f"memory_lag_{lag}" in featured.columns

    # Verify rolling averages
    assert "cpu_roll_mean_1m" in featured.columns
    assert "cpu_roll_mean_5m" in featured.columns
    assert "cpu_roll_mean_15m" in featured.columns
    assert "memory_roll_mean_1m" in featured.columns

    # Verify rolling volatility (std)
    assert "cpu_roll_std_5m" in featured.columns
    assert "memory_roll_std_5m" in featured.columns

    # Verify trend feature
    assert "cpu_trend" in featured.columns
    assert "memory_trend" in featured.columns

    # Verify no NaN values in generated features
    for col in processor.FEATURE_COLS:
        assert not featured[col].isnull().any(), f"NaN found in feature {col}"


# ============================================================================
# 3. Baseline Forecasting Test
# ============================================================================


def test_baseline_forecasting():
    """Verify that baseline moving average computes valid MAE and RMSE."""
    forecaster = ResourceForecaster(min_samples=10)
    y_train = pd.Series([20.0, 22.0, 21.0, 23.0, 24.0, 22.0, 25.0])
    y_test = pd.Series([26.0, 27.0, 28.0])

    mae, rmse = forecaster._evaluate_baseline(y_train, y_test, window=3)

    assert isinstance(mae, float)
    assert isinstance(rmse, float)
    assert mae >= 0.0
    assert rmse >= mae  # RMSE is always >= MAE


# ============================================================================
# 4. Random Forest Training & Prediction Test
# ============================================================================


def test_random_forest_training_and_prediction():
    """Verify that Random Forest trains, evaluates, and predicts future resource utilization."""
    df = generate_synthetic_dataframe(n_samples=50)

    with tempfile.TemporaryDirectory() as tmp_dir:
        forecaster = ResourceForecaster(min_samples=30, model_dir=tmp_dir)

        # Train CPU model
        rf, evaluation, metadata = forecaster.train_model(df, metric="cpu")

        assert rf is not None
        assert evaluation is not None
        assert metadata is not None
        assert metadata.model_type == "RandomForestRegressor"
        assert evaluation.model_mae >= 0.0
        assert evaluation.model_rmse >= 0.0
        assert metadata.training_samples > 0
        assert metadata.test_samples > 0

        # Forecast future points
        response = forecaster.forecast_metric(df, metric="cpu", horizons_seconds=[60, 300, 900])

        assert isinstance(response, PredictionResponse)
        assert response.status == "success"
        assert response.method_used == "random_forest"
        assert len(response.predictions) == 3

        for pt in response.predictions:
            assert 0.0 <= pt.predicted_value <= 100.0
            assert pt.lower_bound is not None and 0.0 <= pt.lower_bound <= 100.0
            assert pt.upper_bound is not None and 0.0 <= pt.upper_bound <= 100.0
            assert pt.target_timestamp > response.timestamp


# ============================================================================
# 5. Forecast Evaluation Comparison Test
# ============================================================================


def test_forecast_evaluation_comparison():
    """Verify model comparison against baseline metrics."""
    df = generate_synthetic_dataframe(n_samples=45)
    with tempfile.TemporaryDirectory() as tmp_dir:
        forecaster = ResourceForecaster(min_samples=25, model_dir=tmp_dir)
        _, evaluation, _ = forecaster.train_model(df, metric="memory")

        assert evaluation is not None
        assert evaluation.model_mae is not None
        assert evaluation.baseline_mae is not None
        assert evaluation.model_rmse is not None
        assert evaluation.baseline_rmse is not None


# ============================================================================
# 6. Insufficient Historical Data Handling Test
# ============================================================================


def test_insufficient_historical_data_handling():
    """Verify graceful handling when insufficient historical records exist."""
    forecaster = ResourceForecaster(min_samples=40)

    # Test 1: Empty DataFrame
    empty_df = pd.DataFrame()
    resp_empty = forecaster.forecast_metric(empty_df, metric="cpu")
    assert resp_empty.status == "insufficient_data"
    assert "Insufficient historical data" in resp_empty.message
    assert resp_empty.predictions == []
    assert resp_empty.method_used == "none"

    # Test 2: Few records (less than required min_samples)
    sparse_df = generate_synthetic_dataframe(n_samples=8)
    resp_sparse = forecaster.forecast_metric(sparse_df, metric="cpu")
    assert resp_sparse.status == "insufficient_data"
    assert "Insufficient historical data" in resp_sparse.message
    assert resp_sparse.predictions == []
    assert resp_sparse.method_used == "none"

    # Test 3: Forecast summary with insufficient data
    summary = forecaster.forecast_summary(sparse_df)
    assert isinstance(summary, PredictionSummary)
    assert summary.status == "insufficient_data"
    assert "Insufficient historical data" in summary.summary


# ============================================================================
# 7. Rule-Based Anomaly Detection Test
# ============================================================================


def test_rule_based_anomaly_detection():
    """Verify rule thresholds detect CPU, RAM, Disk, and Network anomalies with correct structure."""
    detector = AnomalyDetector(
        cpu_warning=70.0,
        cpu_critical=88.0,
        memory_warning=75.0,
        memory_critical=90.0,
        disk_warning=80.0,
        disk_critical=92.0,
        net_speed_spike=20000000.0,
    )

    now = datetime.now(timezone.utc)

    # Critical CPU Snapshot
    snap_cpu_crit = create_synthetic_snapshot(now, cpu=94.0, mem=40.0, disk=40.0)
    anoms = detector.check_rules(snap_cpu_crit)
    assert any(a.metric_name == "cpu" and a.severity == "Critical" for a in anoms)
    crit_anom = next(a for a in anoms if a.severity == "Critical")
    assert crit_anom.observed_value == 94.0
    assert "CPU" in crit_anom.explanation
    assert len(crit_anom.recommended_action) > 0

    # Warning Memory Snapshot
    snap_mem_warn = create_synthetic_snapshot(now, cpu=30.0, mem=78.0, disk=40.0)
    anoms_mem = detector.check_rules(snap_mem_warn)
    assert any(a.metric_name == "memory" and a.severity == "Medium" for a in anoms_mem)

    # Critical Disk Snapshot
    snap_disk_crit = create_synthetic_snapshot(now, cpu=30.0, mem=40.0, disk=95.0)
    anoms_disk = detector.check_rules(snap_disk_crit)
    assert any(a.metric_name == "disk" and a.severity == "Critical" for a in anoms_disk)

    # Network Spike Snapshot
    snap_net_spike = create_synthetic_snapshot(now, cpu=30.0, mem=40.0, upload=35000000.0)
    anoms_net = detector.check_rules(snap_net_spike)
    assert any(a.metric_name == "network" and a.severity == "Medium" for a in anoms_net)


# ============================================================================
# 8. Isolation Forest Anomaly Detection Test
# ============================================================================


def test_isolation_forest_anomaly_detection():
    """Verify Isolation Forest detects multivariate outlier patterns when sufficient data exists."""
    detector = AnomalyDetector(iso_min_samples=30, iso_contamination=0.08)

    # Build 40 normal baseline samples
    normal_df = generate_synthetic_dataframe(n_samples=40, base_cpu=20.0, base_mem=35.0)

    # Inject extreme outlier at the end
    outlier_row = {
        "id": 41,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_percent": 99.0,
        "cpu_cores_logical": 4,
        "memory_percent": 98.0,
        "memory_used_bytes": 15000000000,
        "memory_total_bytes": 16000000000,
        "disk_percent": 97.0,
        "disk_used_bytes": 480000000000,
        "disk_total_bytes": 500000000000,
        "bytes_sent": 500000000,
        "bytes_recv": 500000000,
        "upload_speed_bps": 80000000.0,
        "download_speed_bps": 80000000.0,
    }
    df_with_outlier = pd.concat([normal_df, pd.DataFrame([outlier_row])], ignore_index=True)

    anomalies = detector.check_isolation_forest(df_with_outlier)
    assert len(anomalies) > 0
    iso_anom = anomalies[0]
    assert iso_anom.detection_method == "isolation_forest"
    assert iso_anom.anomaly_score is not None
    assert iso_anom.severity in ["Medium", "High"]
    assert "Isolation Forest" in iso_anom.explanation


# ============================================================================
# 9. Predictive Risk Classification Test
# ============================================================================


def test_risk_classification():
    """Verify that RiskAnalyzer categorizes risk levels accurately based on metrics and models."""
    analyzer = RiskAnalyzer()
    now = datetime.now(timezone.utc)

    # Normal State
    snap_normal = create_synthetic_snapshot(now, cpu=18.0, mem=32.0, disk=45.0)
    risk_normal = analyzer.evaluate_risk(snap_normal)
    assert isinstance(risk_normal, PredictiveRiskResponse)
    assert risk_normal.risk_status == "Normal"
    assert risk_normal.risk_score < 45.0

    # Warning State (Moderate CPU)
    snap_warn = create_synthetic_snapshot(now, cpu=65.0, mem=50.0, disk=50.0)
    risk_warn = analyzer.evaluate_risk(snap_warn)
    assert risk_warn.risk_status in ["Warning", "High Risk"]

    # Critical State (High CPU + High RAM)
    snap_crit = create_synthetic_snapshot(now, cpu=94.0, mem=95.0, disk=90.0)
    risk_crit = analyzer.evaluate_risk(snap_crit)
    assert risk_crit.risk_status == "Critical"
    assert risk_crit.risk_score >= 80.0
    assert len(risk_crit.recommendations) > 0

