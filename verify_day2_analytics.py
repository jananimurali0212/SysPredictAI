"""End-to-end verification script for SysPredictAI Day 2 endpoints and models against a live FastAPI server."""
import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.request
import websockets


def make_request(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "SysPredictAI-Day2-Verification/1.0"})
    with urllib.request.urlopen(req, timeout=10) as response:
        return response.getcode(), json.loads(response.read().decode("utf-8"))


async def test_websocket_stream(ws_url: str):
    print("Connecting to real-time WebSocket stream at %s..." % ws_url)
    async with websockets.connect(ws_url) as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=6.0)
        data = json.loads(msg)
        print(" -> WebSocket Snapshot: CPU=%.1f%%, RAM=%.1f%%, Disk=%.1f%%, Upload=%.1f B/s, Download=%.1f B/s" % (
            data["cpu"]["utilization_percent"],
            data["memory"]["utilization_percent"],
            data["disk"]["utilization_percent"],
            data["network"]["upload_speed_bps"],
            data["network"]["download_speed_bps"],
        ))
        assert "cpu" in data and "memory" in data and "disk" in data and "network" in data
        return True


def run_day2_verification():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = sys.executable

    server_cmd = [
        python_exe,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--log-level",
        "warning",
    ]

    print("=" * 75)
    print("STARTING LIVE FASTAPI SERVER (UVICORN) ON 127.0.0.1:8000...")
    print("=" * 75)

    server_process = subprocess.Popen(server_cmd, cwd=base_dir)

    try:
        # Wait up to 10 seconds for server to be responsive
        server_ready = False
        for attempt in range(25):
            try:
                code, data = make_request("http://127.0.0.1:8000/api/health")
                if code == 200:
                    server_ready = True
                    break
            except Exception:
                time.sleep(0.4)

        if not server_ready:
            raise RuntimeError("FastAPI live server failed to respond on http://127.0.0.1:8000/api/health")

        print("[OK] FastAPI server is live and responsive!\n")

        # 1. Day 1 Regression Check: Health, Current Metrics, History, Processes, System Info
        print("--- 1. VERIFYING DAY 1 CORE TELEMETRY ENDPOINTS ---")
        code, health = make_request("http://127.0.0.1:8000/api/health")
        print(" [OK] GET /api/health -> status=%s, uptime=%.1fs, collectors=%s, db=%s" % (
            health["status"], health["uptime_seconds"], health["collectors_healthy"], health["database_healthy"]
        ))
        assert health["status"] in ["healthy", "degraded"]

        code, current = make_request("http://127.0.0.1:8000/api/metrics/current")
        print(" [OK] GET /api/metrics/current -> CPU=%.1f%%, RAM=%.1f%%, Disk=%.1f%%, Upload=%.1f B/s, Download=%.1f B/s" % (
            current["cpu"]["utilization_percent"],
            current["memory"]["utilization_percent"],
            current["disk"]["utilization_percent"],
            current["network"]["upload_speed_bps"],
            current["network"]["download_speed_bps"],
        ))

        code, history = make_request("http://127.0.0.1:8000/api/metrics/history?limit=5")
        print(" [OK] GET /api/metrics/history?limit=5 -> count=%d snapshots retrieved" % history["count"])
        assert history["count"] > 0

        code, procs = make_request("http://127.0.0.1:8000/api/processes?limit=3&sort_by=cpu")
        print(" [OK] GET /api/processes?limit=3 -> top proc: %s (PID %d, CPU %.1f%%)" % (
            procs["processes"][0]["name"], procs["processes"][0]["pid"], procs["processes"][0]["cpu_percent"]
        ))

        code, sys_info = make_request("http://127.0.0.1:8000/api/system/info")
        print(" [OK] GET /api/system/info -> Host: %s (%s %s, %d logical cores)" % (
            sys_info["hostname"], sys_info["os_name"], sys_info["architecture"], sys_info["logical_cores"]
        ))

        # 2. Day 2 Machine Learning & Predictive Analytics Endpoints
        print("\n--- 2. VERIFYING DAY 2 PREDICTIVE ANALYTICS ENDPOINTS ---")

        # Wait a couple of seconds to accumulate some metric points
        print("Allowing background collector to log metric snapshots...")
        time.sleep(3.0)

        # GET /api/predictions/cpu
        print("\nTesting GET /api/predictions/cpu:")
        code, cpu_pred = make_request("http://127.0.0.1:8000/api/predictions/cpu?horizons=60,300,900")
        print(" Status Code: %d" % code)
        print(" Metric: %s | Status: %s | Method: %s" % (cpu_pred["metric"], cpu_pred["status"], cpu_pred["method_used"]))
        print(" Message: %s" % cpu_pred["message"])
        print(" Current Value: %s%%" % cpu_pred.get("current_value"))
        if cpu_pred["predictions"]:
            for pt in cpu_pred["predictions"]:
                print("  -> Horizon: %ds (%s) | Predicted: %.1f%% [Bounds: %.1f%% - %.1f%%]" % (
                    pt["horizon_seconds"], pt["target_timestamp"], pt["predicted_value"],
                    pt.get("lower_bound", 0), pt.get("upper_bound", 100)
                ))
        assert cpu_pred["status"] in ["success", "insufficient_data"]

        # GET /api/predictions/memory
        print("\nTesting GET /api/predictions/memory:")
        code, mem_pred = make_request("http://127.0.0.1:8000/api/predictions/memory?horizons=60,300,900")
        print(" Status Code: %d" % code)
        print(" Metric: %s | Status: %s | Method: %s" % (mem_pred["metric"], mem_pred["status"], mem_pred["method_used"]))
        print(" Message: %s" % mem_pred["message"])
        assert mem_pred["status"] in ["success", "insufficient_data"]

        # GET /api/predictions/summary
        print("\nTesting GET /api/predictions/summary:")
        code, summary = make_request("http://127.0.0.1:8000/api/predictions/summary")
        print(" Status Code: %d" % code)
        print(" Status: %s" % summary["status"])
        print(" Summary Text: %s" % summary["summary"])
        assert "cpu_forecast" in summary and "memory_forecast" in summary

        # GET /api/anomalies
        print("\nTesting GET /api/anomalies:")
        code, anomalies = make_request("http://127.0.0.1:8000/api/anomalies")
        print(" Status Code: %d" % code)
        print(" Total Anomalies Detected: %d" % anomalies["total_anomalies"])
        print(" Isolation Forest Active: %s" % anomalies["isolation_forest_enabled"])
        if anomalies["anomalies"]:
            for a in anomalies["anomalies"]:
                print("  -> [%s] %s on %s: Observed %.1f (Method: %s) - %s" % (
                    a["severity"], a["anomaly_id"], a["metric_name"], a["observed_value"], a["detection_method"], a["explanation"]
                ))
        else:
            print("  -> System operating within normal thresholds. Zero active anomalies.")
        assert "total_anomalies" in anomalies

        # GET /api/risk
        print("\nTesting GET /api/risk:")
        code, risk = make_request("http://127.0.0.1:8000/api/risk")
        print(" Status Code: %d" % code)
        print(" Overall Risk Status: %s (Composite Score: %.1f / 100.0)" % (risk["risk_status"], risk["risk_score"]))
        print(" Trends: CPU=%s, RAM=%s (%s)" % (
            risk["recent_cpu_trend"], risk["recent_memory_trend"], risk["breakdown"]["trend_description"]
        ))
        print(" Breakdown: CPU=%s, RAM=%s, Disk=%s, Network=%s, Forecast=%s" % (
            risk["breakdown"]["cpu_status"],
            risk["breakdown"]["memory_status"],
            risk["breakdown"]["disk_status"],
            risk["breakdown"]["network_status"],
            risk["breakdown"]["forecast_risk"],
        ))
        print(" Recommendations:")
        for r in risk["recommendations"]:
            print("  - %s" % r)
        assert risk["risk_status"] in ["Normal", "Warning", "High Risk", "Critical"]

        # WebSocket Streaming
        print("\nTesting WebSocket /ws/metrics:")
        ws_ok = asyncio.run(test_websocket_stream("ws://127.0.0.1:8000/ws/metrics"))
        assert ws_ok is True

        print("\n" + "=" * 75)
        print("ALL DAY 1 AND DAY 2 API ENDPOINTS VERIFIED SUCCESSFULLY AGAINST LIVE SERVER!")
        print("=" * 75)

    finally:
        print("\nGracefully terminating live server process...")
        server_process.terminate()
        server_process.wait(timeout=5)
        print("Server shutdown complete.")


if __name__ == "__main__":
    run_day2_verification()

