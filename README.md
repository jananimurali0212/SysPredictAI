# SysPredictAI

<p align="center">
  <strong>AI-Powered Real-Time System Monitoring and Predictive Analytics Platform</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white" alt="React" />
  <img src="https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwindcss&logoColor=white" alt="Tailwind CSS" />
  <img src="https://img.shields.io/badge/AI-Google%20Gemini-4285F4?logo=google&logoColor=white" alt="Gemini AI" />
  <img src="https://img.shields.io/badge/Machine%20Learning-Scikit--Learn-F7931E?logo=scikit-learn&logoColor=white" alt="Scikit-Learn" />
  <img src="https://img.shields.io/badge/Tests-35%2F35%20Passing-emerald?logo=pytest&logoColor=white" alt="Tests" />
  <img src="https://img.shields.io/badge/License-MIT-purple" alt="License" />
</p>

---

## 📌 Overview

**SysPredictAI** is a high-performance local system monitoring and AI predictive analytics platform. It collects granular hardware metrics directly from the host operating system via non-blocking hardware probes, persists time-series history in an embedded SQLite database configured with Write-Ahead Logging (WAL), forecasts CPU and RAM utilization using **Random Forest Regressors**, detects anomalies via rule-based filters and **Isolation Forest**, provides **Gemini AI diagnostic insights**, and features a modern, responsive **React + Vite + Tailwind CSS dashboard**.

---

## 🏗️ Architecture & Project Structure

```text
SysPredictAI/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI entry point, static frontend mount, CORS & logging
│   ├── config.py                 # Pydantic Settings with .env, ML & Gemini configurations
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── system_collector.py   # psutil-based CPU, RAM, Disk & Network collectors
│   │   └── process_collector.py  # Fault-tolerant OS process table collector
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── data_processor.py     # Historical data extraction, cleaning & feature engineering
│   │   ├── forecaster.py         # Baseline & Random Forest Regressor resource forecasting
│   │   ├── anomaly_detector.py   # Rule-based thresholding & Scikit-Learn Isolation Forest
│   │   └── risk_analyzer.py      # Composite risk engine (Normal, Warning, High Risk, Critical)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py             # REST endpoints (telemetry, ML, AI) & WebSocket handler
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py         # Google Gemini AI & grounded telemetry diagnostic engine
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
│   │   ├── analytics.py          # Pydantic v2 schemas for ML forecasts, anomalies & risk
│   │   └── ai.py                 # Pydantic v2 schemas for Gemini AI queries & summaries
│   └── static/
│       └── dashboard.html        # Fallback static visual dashboard
├── frontend/                     # Day 3 React + Vite Frontend Application
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/           # MetricCard, StatusBadge, LoadingState, ErrorAlert
│   │   │   ├── layout/           # Sidebar, Header, MainLayout
│   │   │   └── pages/            # 7 Dashboard Pages:
│   │   │       ├── Overview.jsx          # Executive summary, key metrics, live mini-chart
│   │   │       ├── LiveMonitoring.jsx    # Real-time WebSocket streaming, Recharts waveforms
│   │   │       ├── ProcessMonitoring.jsx # Searchable, sortable process table
│   │   │       ├── Predictions.jsx       # Forecast vs actual, Random Forest MAE/RMSE
│   │   │       ├── AnomalyDetection.jsx  # Multi-severity alert log & Isolation Forest
│   │   │       ├── AIInsights.jsx        # Gemini diagnostic Q&A assistant
│   │   │       └── Settings.jsx          # Cadence, alert threshold sliders, local preferences
│   │   ├── services/
│   │   │   ├── api.js            # Centralized backend HTTP client
│   │   │   └── websocket.js      # Resilient WebSocket client with auto-reconnection
│   │   ├── App.jsx               # Navigation state switcher
│   │   ├── index.css             # Tailwind CSS & custom scrollbar styles
│   │   └── main.jsx              # Application DOM root
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── index.html
├── saved_models/                 # Serialized model artifacts (.joblib) & metadata (.json)
├── tests/
│   ├── test_metrics.py           # Unit tests for hardware collectors & SQLite
│   ├── test_api.py               # Integration tests for core REST endpoints & WebSockets
│   ├── test_analytics.py         # Unit tests for ML features, forecaster, anomalies & risk
│   ├── test_analytics_api.py     # Integration tests for Day 2 ML REST endpoints
│   └── test_ai_insights.py       # Integration tests for Day 3 Gemini AI endpoints
├── verify_live_server.py         # Day 1 live server verification suite
├── verify_day2_analytics.py      # Day 2 ML & predictions verification suite
├── verify_day3_frontend.py       # Day 3 end-to-end full platform verification suite
├── requirements.txt              # Backend Python dependencies
├── pytest.ini                    # Pytest configuration
├── .env.example                  # Environment configuration template
└── README.md                     # Project documentation
```

---

## 🎨 Day 3: Frontend Dashboard & AI Insights

### 1. Modern Dark Navy UI
- Built with **React 18**, **Vite**, **Tailwind CSS**, and **Lucide React** icons.
- Cohesive dark navy color palette:
  - Background: Deep Navy (`#0B0F19`)
  - Cards: Surface Navy (`#111827`)
  - Accent: Vibrant Blue (`#3B82F6`)
  - Status Indicators: Normal (`#10B981`), Warning (`#F59E0B`), Critical (`#EF4444`)
- Fully responsive across desktop, tablet, and mobile layouts.

### 2. 7 Dedicated Dashboard Pages
1. **Overview**: Executive status statement, key hardware cards, live mini-chart, recent anomaly feed, and instant AI summary.
2. **Live Monitoring**: Real-time WebSocket streaming at 1-second cadence, dual area/line charts, per-core CPU load distribution bars, and network upload/download bandwidth.
3. **Process Monitoring**: Top active processes table with real-time PID, CPU %, RAM %, and RSS memory, instant name/PID search filtering, and sorting toggles.
4. **Predictions**: Short-term CPU and RAM regression projections (60s, 300s, 900s), historical vs. predicted comparison chart with confidence bands, model evaluation metrics (MAE, RMSE, baseline comparisons), and clear statistical estimate disclaimers.
5. **Anomaly Detection**: Active anomaly alerts with severity filters (`All`, `Critical`, `High`, `Medium`, `Low`), observed values, baseline references, anomaly scores, and remediation advice.
6. **AI Insights**: Interactive Gemini AI assistant answering questions like *"Why is my CPU usage high?"*, *"Which process is consuming the most resources?"*, or custom inquiries, with strict separation between directly observed facts, possible causes, and recommended actions.
7. **Settings**: Configurable polling cadence, interactive alert threshold sliders (CPU/RAM warning & critical), compact table mode, and local storage persistence.

### 3. Gemini AI Diagnostics & Grounding Policy (`app/services/ai_service.py`)
- **Backend Protected**: The Gemini API key remains securely stored in the backend environment (`GEMINI_API_KEY`). It is never exposed in frontend bundles.
- **Strict Telemetry Grounding**: The AI model is supplied real hardware metrics, active processes, and anomaly records.
- **Fail-Safe Telemetry Fallback**: If `GEMINI_API_KEY` is not configured, the platform automatically switches to an intelligent local rule-grounded telemetry reasoning engine so diagnostics always function without interruption.

---

## 📡 REST API Reference

### Core Telemetry (Day 1)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status, collector status, and DB state |
| `GET` | `/api/metrics/current` | Real-time CPU, RAM, Disk, and Network speeds |
| `GET` | `/api/metrics/history` | Historical telemetry snapshots from SQLite |
| `GET` | `/api/processes` | Active processes sorted by `cpu` or `memory` |
| `GET` | `/api/system/info` | Host hardware specifications, architecture, and uptime |
| `WS` | `/ws/metrics` | Real-time WebSocket streaming socket (~1s interval) |

### Predictive Analytics (Day 2)
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/predictions/cpu` | Short-term CPU utilization forecast (60s, 300s, 900s) |
| `GET` | `/api/predictions/memory` | Short-term RAM utilization forecast (60s, 300s, 900s) |
| `GET` | `/api/predictions/summary` | Executive synthesized resource forecast |
| `GET` | `/api/anomalies` | Detected system anomalies from rule filters and Isolation Forest |
| `GET` | `/api/risk` | Holistic predictive risk assessment (`Normal`, `Warning`, `High Risk`, `Critical`) |

### Gemini AI Insights (Day 3)
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/insights/query` | Ask Gemini AI performance questions with telemetry grounding |
| `GET` | `/api/insights/summary` | Automated executive system health statement |

---

## 🚀 Running the Application

### 1. Start the Backend Server
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Built-in React Dashboard**: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)

### 2. Start the React Frontend in Development Mode
```powershell
cd frontend
npm run dev
```
- **Vite Live Dashboard**: [http://localhost:5173](http://localhost:5173)

---

## 🧪 Testing & Verification

### Run Complete Automated Test Suite (35 Tests)
```powershell
python -m pytest -v
```
*Executes all **35 automated tests** covering Day 1 telemetry collectors, Day 2 Random Forest and Isolation Forest modules, and Day 3 Gemini AI insights.*

### Run Day 3 End-to-End Verification Script
```powershell
python verify_day3_frontend.py
```
*Validates the live backend, Gemini AI queries, React frontend distribution, and WebSocket streaming.*

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
