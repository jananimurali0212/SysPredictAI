# SysPredictAI

<p align="center">
  <strong>AI-Powered Real-Time System Monitoring and Predictive Analytics Platform</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-F7931E?logo=scikit-learn&logoColor=white" alt="Scikit-Learn" />
  <img src="https://img.shields.io/badge/Data%20Processing-Pandas-150458?logo=pandas&logoColor=white" alt="Pandas" />
  <img src="https://img.shields.io/badge/Storage-SQLite%20WAL-003B57?logo=sqlite&logoColor=white" alt="SQLite WAL" />
  <img src="https://img.shields.io/badge/Streaming-WebSockets-4B5563?logo=socketdotio&logoColor=white" alt="WebSockets" />
  <img src="https://img.shields.io/badge/Tests-29%2F29%20Passing-emerald?logo=pytest&logoColor=white" alt="Tests" />
  <img src="https://img.shields.io/badge/License-MIT-purple" alt="License" />
</p>

---

## 📌 Overview

**SysPredictAI** is a high-performance local system monitoring and AI predictive analytics platform. It collects granular hardware metrics directly from the host operating system via non-blocking hardware probes, persists time-series history in an embedded SQLite database configured with Write-Ahead Logging (WAL), and features a complete **Machine Learning and Predictive Analytics Engine** that generates time-series feature sets, forecasts CPU and RAM utilization using **Random Forest Regressors** and baseline models, detects anomalies via rule-based filters and **Isolation Forest**, and computes holistic predictive system risk levels.

---

## 🏗️ Architecture & Project Structure

```text
SysPredictAI/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI entry point, lifespan, CORS & structured logging
│   ├── config.py                 # Pydantic Settings with .env and ML parameters
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── system_collector.py   # psutil-based CPU, RAM, Disk & Network collectors
│   │   └── process_collector.py  # Fault-tolerant OS process table collector
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── data_processor.py     # Historical data retrieval, cleaning & feature engineering
│   │   ├── forecaster.py         # Baseline & Random Forest Regressor resource forecasting
│   │   ├── anomaly_detector.py   # Rule-based thresholding & Scikit-Learn Isolation Forest
│   │   └── risk_analyzer.py      # Composite risk engine (Normal, Warning, High Risk, Critical)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py             # REST endpoints (telemetry + ML) & WebSocket handler
│   ├── services/
│   │   ├── __init__.py
│   │   └── monitoring_service.py # Telemetry coordinator, worker daemon & ML orchestrator
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                 # Thread-safe SQLite persistence manager with WAL mode
│   │   └── models.py             # SQLite schema DDL and index specifications
│   ├── websocket/
│   │   ├── __init__.py
│   │   └── manager.py            # Multi-client WebSocket connection manager
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── metrics.py            # Pydantic v2 schemas for telemetry & responses
│   │   └── analytics.py          # Pydantic v2 schemas for ML forecasts, anomalies & risk
│   └── static/
│       └── dashboard.html        # Real-time visual web dashboard
├── saved_models/                 # Serialized model artifacts (.joblib) & metadata (.json)
├── tests/
│   ├── test_metrics.py           # Unit tests for hardware collectors & SQLite
│   ├── test_api.py               # Integration tests for core REST endpoints & WebSockets
│   ├── test_analytics.py         # Unit tests for ML features, forecaster, anomalies & risk
│   └── test_analytics_api.py     # Integration tests for Day 2 ML REST endpoints
├── verify_live_server.py         # Day 1 live server end-to-end verification suite
├── verify_day2_analytics.py      # Day 2 end-to-end verification of all ML endpoints
├── system_health_audit.py        # Comprehensive live health audit script
├── requirements.txt              # Project dependencies
├── pytest.ini                    # Pytest test discovery & pythonpath configuration
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore specifications
├── LICENSE                       # Project license
└── README.md                     # Project manual
```

---

## 🤖 Day 2: Machine Learning & Predictive Analytics Engine

### 1. Historical Data Processing & Feature Engineering (`app/ml/data_processor.py`)
- **Direct Database Extraction**: Extracts real persisted telemetry into Pandas DataFrames.
- **Chronological Sorting & Cleaning**: Sorts timestamps chronologically, deduplicates records, and cleans missing values without fabricating artificial metrics.
- **Engineered Time-Series Features**:
  - Current CPU (`cpu_percent`) and Memory (`memory_percent`) utilization.
  - **Lag Features**: Step lags at $t-1$, $t-2$, $t-3$, and $t-5$ to capture momentum.
  - **Rolling Averages**: 1-minute (`60s`), 5-minute (`300s`), and 15-minute (`900s`) moving averages.
  - **Rolling Volatility**: 5-minute rolling standard deviation reflecting utilization jitter.
  - **Recent Utilization Trend**: Delta differentials comparing current utilization against recent baselines.

### 2. Resource Forecasting (`app/ml/forecaster.py`)
- **Baseline Forecasting**: Moving average and persistence models providing standard reference benchmarks.
- **Random Forest Regressor**:
  - Trains dedicated regressors for CPU and Memory using `RandomForestRegressor(n_estimators=50, max_depth=6)`.
  - **Strict Chronological Splitting**: Chronological 80/20 train/test split preserving temporal integrity (never randomly shuffled).
  - **Performance Evaluation**: Computes **Mean Absolute Error (MAE)** and **Root Mean Squared Error (RMSE)** for both the trained Random Forest and the baseline model, logging percentage improvements.
  - **Configurable Future Horizons**: Generates forward-looking projections for short-term intervals (e.g. 60s, 300s, 900s) with confidence bounds.
  - **Bound Enforcement**: All predictions are clipped to valid limits $[0.0, 100.0]\%$.
  - **Insufficient Data Protection**: If collected samples fall below the configurable threshold (`ML_MIN_TRAINING_SAMPLES`, default 30), returns status `"insufficient_data"` with a clear message and zero fabricated predictions.
  - **Model Persistence**: Serializes trained models to `saved_models/{metric}_rf_model.joblib` alongside structured metadata `saved_models/{metric}_metadata.json`.

### 3. Anomaly Detection (`app/ml/anomaly_detector.py`)
- **Dual-Layer Detection Strategy**:
  1. **Rule-Based Thresholds**: Flags instant breaches and rapid surges:
     - CPU utilization warning ($\ge 75\%$) and critical ($\ge 90\%$).
     - Sudden CPU spike ($+35\%$ jump over 10-sample moving average).
     - Memory utilization warning ($\ge 80\%$) and critical ($\ge 92\%$).
     - Disk volume capacity warning ($\ge 85\%$) and critical ($\ge 95\%$).
     - Network transfer burst ($\ge 50\text{ MB/s}$ or configurable threshold).
  2. **Multivariate Isolation Forest**:
     - Fits `IsolationForest(contamination=0.05)` across multi-dimensional feature space (`cpu_percent`, `memory_percent`, `disk_percent`, `upload_speed_bps`, `download_speed_bps`) when $\ge 40$ samples exist.
     - Identifies multivariate outlier patterns with calculated decision scores and isolates the primary deviating metric.
- **Structured Anomaly Output**:
  - `anomaly_id`: Unique identifier
  - `timestamp`: UTC event timestamp
  - `metric_name`: Hardware component
  - `observed_value`: Exact numeric measurement
  - `severity`: `Low`, `Medium`, `High`, or `Critical`
  - `explanation`: Contextual description
  - `recommended_action`: Actionable remediation guidance

### 4. Predictive Risk Analysis (`app/ml/risk_analyzer.py`)
- Holistically evaluates:
  - Current CPU and RAM utilization.
  - Short-term trend trajectories (`rising`, `declining`, `stable`).
  - ML forward-looking forecasted resource pressure.
  - Count and severities of detected anomalies.
- **Derived Risk Status**:
  - `Normal`: Stable operation within baseline limits.
  - `Warning`: Moderate elevated load or single medium anomaly.
  - `High Risk`: Approaching operational thresholds or elevated ML forecast.
  - `Critical`: Saturated hardware, critical threshold breach, or severe active anomalies.
- Produces a **composite risk score** ($0.0 - 100.0$), component-level status breakdowns, and prioritized recommendations.

---

## 📡 REST API Reference

### Day 1 Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status, collector status, and DB state |
| `GET` | `/api/metrics/current` | Real-time CPU, RAM, Disk, and Network speeds |
| `GET` | `/api/metrics/history` | Historical telemetry snapshots from SQLite |
| `GET` | `/api/processes` | Active processes sorted by `cpu` or `memory` |
| `GET` | `/api/system/info` | Host hardware specifications, architecture, and uptime |
| `WS` | `/ws/metrics` | Real-time WebSocket streaming socket (~1s interval) |

### Day 2 Machine Learning & Predictive Analytics Endpoints

#### 1. CPU Utilization Forecast
```http
GET /api/predictions/cpu?horizons=60,300,900
```
```json
{
  "metric": "cpu",
  "status": "success",
  "message": "Resource forecast generated successfully using Random Forest Regressor.",
  "timestamp": "2026-11-13T10:45:58.939565Z",
  "current_value": 30.5,
  "method_used": "random_forest",
  "predictions": [
    {
      "horizon_seconds": 60,
      "target_timestamp": "2026-11-13T10:46:58.939565Z",
      "predicted_value": 33.5,
      "lower_bound": 25.04,
      "upper_bound": 41.96
    },
    {
      "horizon_seconds": 300,
      "target_timestamp": "2026-11-13T10:50:58.939565Z",
      "predicted_value": 32.98,
      "lower_bound": 24.52,
      "upper_bound": 41.44
    }
  ],
  "evaluation": {
    "model_mae": 8.461,
    "model_rmse": 10.167,
    "baseline_mae": 2.576,
    "baseline_rmse": 3.162
  }
}
```

#### 2. RAM Memory Forecast
```http
GET /api/predictions/memory?horizons=60,300,900
```
*Returns identical structure for memory utilization.*

#### 3. Prediction Summary
```http
GET /api/predictions/summary
```
```json
{
  "timestamp": "2026-11-13T10:45:58.939565Z",
  "status": "success",
  "cpu_forecast": { ... },
  "memory_forecast": { ... },
  "summary": "CPU forecast: 33.5% utilization expected in 60s. Memory forecast: 90.8% utilization expected in 60s."
}
```

#### 4. Anomaly Detection
```http
GET /api/anomalies
```
```json
{
  "timestamp": "2026-11-13T10:45:37.892014Z",
  "total_anomalies": 1,
  "isolation_forest_enabled": true,
  "anomalies": [
    {
      "anomaly_id": "anom_mem_warn_1794566737",
      "timestamp": "2026-11-13T10:45:37.892014Z",
      "metric_name": "memory",
      "observed_value": 90.4,
      "threshold_or_baseline": 80.0,
      "anomaly_score": 0.7,
      "detection_method": "rule_based",
      "severity": "Medium",
      "explanation": "RAM utilization (90.4%) exceeded warning threshold (80.0%).",
      "recommended_action": "Review high memory footprint processes."
    }
  ]
}
```

#### 5. Predictive Risk Assessment
```http
GET /api/risk
```
```json
{
  "timestamp": "2026-11-13T10:45:37.912411Z",
  "risk_status": "High Risk",
  "risk_score": 61.8,
  "current_cpu_percent": 30.8,
  "current_memory_percent": 90.5,
  "recent_cpu_trend": "rising",
  "recent_memory_trend": "stable",
  "breakdown": {
    "cpu_status": "Normal",
    "memory_status": "High Risk",
    "disk_status": "Normal",
    "network_status": "Normal",
    "forecast_risk": "Normal",
    "trend_description": "CPU climbing (+18.8%), RAM stable"
  },
  "active_anomalies_count": 1,
  "recommendations": [
    "Memory utilization is high. Free dormant process allocations or add RAM.",
    "[Medium Anomaly] Review high memory footprint processes."
  ]
}
```

---

## 🧪 Testing & Verification

The test suite covers historical data extraction, feature generation, Random Forest regression, baseline comparisons, insufficient data safety, anomaly detection, risk classification, and API response validation.

### Run Automated Pytest Suite
```powershell
python -m pytest -v
```
*Executes all **29 automated tests** across `tests/test_metrics.py`, `tests/test_api.py`, `tests/test_analytics.py`, and `tests/test_analytics_api.py`.*

### Run Live Day 2 Verification Script
```powershell
python verify_day2_analytics.py
```
*Spawns a live FastAPI instance, polls telemetry, validates all 10 REST endpoints and WebSocket streaming, and exercises the ML pipeline with zero mock data.*

### Run Day 1 Verification Suite
```powershell
python verify_live_server.py
```

---

## 🗺️ Project Roadmap

- [x] **Day 1 – Foundation & Monitoring Engine**
  - psutil hardware collectors (CPU, Memory, Disk, Network, Processes)
  - SQLite persistence with WAL mode & Pandas export
  - FastAPI REST backend and `/ws/metrics` streaming
  - Built-in live visual dashboard (`/dashboard`)
  - 100% test coverage and live audit verification
- [x] **Day 2 – Machine Learning & Predictive Analytics**
  - Time-series feature engineering (lags, rolling averages, rolling volatility, trends)
  - Baseline and Random Forest Regressors for CPU and RAM utilization
  - Chronological evaluation with MAE, RMSE, and benchmark comparison
  - Graceful insufficient historical data protection (no fabricated predictions)
  - Dual-layer anomaly detection (Rule-based heuristics + Scikit-Learn Isolation Forest)
  - Multi-factor Predictive Risk Analyzer (`Normal`, `Warning`, `High Risk`, `Critical`)
  - 5 new REST endpoints (`/api/predictions/cpu`, `/api/predictions/memory`, `/api/predictions/summary`, `/api/anomalies`, `/api/risk`)
  - Complete automated test suite (29/29 passing)
- [ ] **Day 3 – Advanced Frontend & Visual Analytics**
  - Interactive multi-horizon forecast charts
  - Anomaly timeline and alert banner widgets
  - Live risk gauges and recommendation action items

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
