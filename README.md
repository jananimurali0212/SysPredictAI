# SysPredictAI

<p align="center">
  <strong>AI-Powered Real-Time System Monitoring and Predictive Analytics Platform</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white" alt="Python Version" />
  <img src="https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Storage-SQLite%20WAL-003B57?logo=sqlite&logoColor=white" alt="SQLite WAL" />
  <img src="https://img.shields.io/badge/Streaming-WebSockets-4B5563?logo=socketdotio&logoColor=white" alt="WebSockets" />
  <img src="https://img.shields.io/badge/Tests-14%2F14%20Passing-emerald?logo=pytest&logoColor=white" alt="Tests" />
  <img src="https://img.shields.io/badge/License-MIT-purple" alt="License" />
</p>

---

## 📌 Overview

**SysPredictAI** is a high-performance, real-time local system monitoring and telemetry engine. It captures granular hardware metrics directly from the host operating system via non-blocking hardware probes, persists time-series history in an embedded SQLite database configured with Write-Ahead Logging (WAL), and broadcasts instantaneous telemetry to connected clients via both REST APIs and real-time WebSockets.

---

## 🏗️ Architecture & Project Structure

```text
AI-System-Monitor/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI entry point, lifespan, CORS & structured logging
│   ├── config.py                # Pydantic Settings with .env support
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── system_collector.py  # psutil-based CPU, RAM, Disk & Network collectors
│   │   └── process_collector.py # Fault-tolerant OS process table collector
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py            # REST endpoints & WebSocket stream handler
│   ├── services/
│   │   ├── __init__.py
│   │   └── monitoring_service.py # Telemetry coordinator, worker daemon & broadcaster
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                # Thread-safe SQLite persistence manager with WAL mode
│   │   └── models.py            # SQLite schema DDL and index specifications
│   ├── websocket/
│   │   ├── __init__.py
│   │   └── manager.py           # Multi-client WebSocket connection manager
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── metrics.py           # Pydantic v2 schemas for telemetry & responses
│   └── static/
│       └── dashboard.html       # Built-in real-time visual web dashboard
├── tests/
│   ├── test_metrics.py          # Unit tests for hardware collectors & SQLite
│   └── test_api.py              # Integration tests for REST endpoints & WebSockets
├── verify_live_server.py        # Live server end-to-end verification suite
├── system_health_audit.py       # Comprehensive 9-point live health audit script
├── requirements.txt             # Project dependencies
├── pytest.ini                   # Pytest test discovery & pythonpath configuration
├── .env.example                 # Environment configuration template
├── .gitignore                   # Git ignore specifications
├── LICENSE                      # Project license
└── README.md                    # Project manual
```

---

## ⚡ Core Engine Features

### 1. CPU Telemetry
- **Overall Utilization**: Non-blocking instantaneous CPU usage percentage.
- **Per-Core Breakdown**: Granular core-by-core load percentages.
- **Topology**: Physical core count and logical thread count.
- **Dynamic Clock Speed**: Current, minimum, and maximum frequencies in MHz (when exposed by hardware).

### 2. RAM Memory Monitoring
- Total physical capacity, used memory, and available memory in bytes and gigabytes.
- Real-time utilization percentage.

### 3. Disk Storage Monitoring
- Storage drive mount detection (`C:\` on Windows, `/` on POSIX).
- Total storage capacity, used space, and free space.
- Live disk utilization percentage.

### 4. Dynamic Network Bandwidth
- Total bytes transmitted and received since boot.
- Real-time **upload speed** (bytes/second) and **download speed** (bytes/second).
- Differential calculation between successive sampling intervals with clock rollover protection.

### 5. Fault-Tolerant Process Inspection
- Lists active processes with PID, Name, CPU %, RAM %, Resident Set Size (RSS), and execution status.
- Safely handles transient processes and access denied scenarios (`psutil.NoSuchProcess`, `psutil.AccessDenied`, `psutil.ZombieProcess`) without crashing.
- Dynamic sorting by `cpu` or `memory`.

### 6. Historical Time-Series Persistence
- Embedded **SQLite** database configured with Write-Ahead Logging (`PRAGMA journal_mode=WAL`) and normal synchrony for non-blocking concurrent reads and writes.
- Automated rolling cleanup based on configurable retention thresholds.
- Native `get_history_df()` helper integrating **Pandas** `read_sql_query` for future predictive modeling.

### 7. Real-Time WebSocket Streaming
- Streaming endpoint at `/ws/metrics` broadcasting system snapshots at a ~1-second interval.
- Multi-client connection pooling, automatic dead socket eviction, and client heartbeat (`ping` $\to$ `pong`) support.

### 8. Built-in Visual Dashboard
- Served directly at `/dashboard` (and `/` in browsers).
- Modern dark-mode UI with live Chart.js utilization trends, per-core utilization bars, hardware gauges, and live updating process table.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11 or higher
- PowerShell (Windows) or Bash (macOS/Linux)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/jananimurali0212/SysPredictAI.git
cd SysPredictAI
```

### 2. Set Up a Virtual Environment
```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
# python3 -m venv .venv
# source .venv/bin/activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Start the Application
```powershell
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🌐 Endpoints & User Interfaces

Once started, access the following interfaces:

| Interface | URL | Description |
|---|---|---|
| 🖥️ **Live Web Dashboard** | **[http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)** | Real-time visual dashboard with live charts and gauges |
| 📖 **Interactive Swagger UI** | **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)** | Test every API endpoint interactively |
| 📚 **ReDoc Documentation** | **[http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)** | Clean specification view of models and endpoints |
| ⚡ **WebSocket Stream** | **`ws://127.0.0.1:8000/ws/metrics`** | Real-time metric streaming socket (~1s interval) |

---

## 📡 REST API Reference

### Health Check
```http
GET /api/health
```
```json
{
  "status": "healthy",
  "timestamp": "2026-11-12T12:06:18.284302Z",
  "version": "1.0.0",
  "uptime_seconds": 124.5,
  "collectors_healthy": true,
  "database_healthy": true
}
```

### Current Telemetry Snapshot
```http
GET /api/metrics/current
```
```json
{
  "timestamp": "2026-11-12T12:15:40.824649Z",
  "cpu": {
    "utilization_percent": 18.5,
    "per_core_utilization": [25.0, 12.5, 18.0, 15.2, 22.1, 10.4, 20.0, 16.3],
    "core_count_physical": 4,
    "core_count_logical": 8,
    "frequency": { "current": 2000.0, "min": null, "max": 2001.0 }
  },
  "memory": {
    "total_bytes": 8215191552,
    "used_bytes": 7401201664,
    "available_bytes": 813989888,
    "utilization_percent": 90.1
  },
  "disk": {
    "mount_point": "C:\\",
    "total_bytes": 294056357888,
    "used_bytes": 185739501568,
    "available_bytes": 108316856320,
    "utilization_percent": 63.2
  },
  "network": {
    "bytes_sent": 822454235,
    "bytes_recv": 1176633939,
    "upload_speed_bps": 143071.66,
    "download_speed_bps": 28954.61
  }
}
```

### Historical Metrics Query
```http
GET /api/metrics/history?limit=100&start_time=2026-11-12T00:00:00Z
```

### Active Processes Table
```http
GET /api/processes?limit=25&sort_by=cpu
```
*`sort_by` accepts `cpu` or `memory`.*

### System Specifications
```http
GET /api/system/info
```

---

## 🧪 Testing & Verification

The project includes unit tests, integration tests, and live server audit scripts:

### Run Automated Pytest Suite
```powershell
.\.venv\Scripts\python -m pytest -v
```
*Runs 14 automated tests covering CPU, RAM, Disk, Network speed calculation, process handling, SQLite persistence, REST endpoints, and WebSocket handshake.*

### Run Live Server Verification
```powershell
.\.venv\Scripts\python verify_live_server.py
```

### Run Comprehensive 9-Point System Audit
```powershell
.\.venv\Scripts\python system_health_audit.py
```

---

## 🗺️ Project Roadmap

- [x] **Day 1 – Foundation & Monitoring Engine**
  - psutil hardware collectors (CPU, Memory, Disk, Network, Processes)
  - SQLite persistence with WAL mode & Pandas export
  - FastAPI REST backend and `/ws/metrics` streaming
  - Built-in live visual dashboard (`/dashboard`)
  - 100% test coverage and live audit verification
- [ ] **Day 2 – Dedicated Frontend & Advanced Visualizations**
  - React + Vite / Streamlit frontend application
  - Historical time-series replay and interactive date range filters
  - Per-process historical tree inspection
- [ ] **Day 3 – AI Predictive Analytics & Anomaly Detection**
  - Machine learning models for resource exhaustion forecasting (RAM/Disk)
  - Anomaly detection algorithms (Z-score / Isolation Forests) for spike alerts
  - Automated threshold alerts and predictive warnings

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
