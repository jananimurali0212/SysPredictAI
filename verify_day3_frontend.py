"""End-to-end Day 3 verification script checking FastAPI backend, Gemini AI endpoints, and React frontend."""
import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.request
import websockets


def make_request(url: str, method: str = "GET", data: dict = None):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "SysPredictAI-Day3-Verification/1.0", "Content-Type": "application/json"},
        method=method,
    )
    payload = json.dumps(data).encode("utf-8") if data else None
    with urllib.request.urlopen(req, data=payload, timeout=10) as response:
        content = response.read().decode("utf-8")
        try:
            return response.getcode(), json.loads(content)
        except Exception:
            return response.getcode(), content


async def test_websocket_stream(ws_url: str):
    print("Testing live WebSocket stream at %s..." % ws_url)
    async with websockets.connect(ws_url) as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=6.0)
        data = json.loads(msg)
        print(" [OK] WebSocket Snapshot Received: CPU=%.1f%%, RAM=%.1f%%, Disk=%.1f%%" % (
            data["cpu"]["utilization_percent"],
            data["memory"]["utilization_percent"],
            data["disk"]["utilization_percent"],
        ))
        assert "cpu" in data and "memory" in data and "disk" in data and "network" in data
        return True


def run_day3_verification():
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
        # Wait for server to become responsive
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
            raise RuntimeError("FastAPI server failed to respond on http://127.0.0.1:8000/api/health")

        print("[OK] FastAPI server is live and responsive!\n")

        # 1. Day 1 & Day 2 Regression Check
        print("--- 1. VERIFYING BACKEND CORE HEALTH & TELEMETRY ---")
        code, health = make_request("http://127.0.0.1:8000/api/health")
        assert code == 200
        print(" [OK] GET /api/health -> status=%s, uptime=%.1fs" % (health["status"], health["uptime_seconds"]))

        code, current = make_request("http://127.0.0.1:8000/api/metrics/current")
        assert code == 200
        print(" [OK] GET /api/metrics/current -> CPU=%.1f%%, RAM=%.1f%%" % (
            current["cpu"]["utilization_percent"], current["memory"]["utilization_percent"]
        ))

        # 2. Day 3 Gemini AI Insights Endpoints
        print("\n--- 2. VERIFYING DAY 3 GEMINI AI INSIGHTS ENDPOINTS ---")

        # Test POST /api/insights/query
        test_q = "Why is my CPU usage high?"
        print("Testing POST /api/insights/query with question: '%s'..." % test_q)
        code, ai_res = make_request(
            "http://127.0.0.1:8000/api/insights/query",
            method="POST",
            data={"question": test_q},
        )
        assert code == 200
        print(" [OK] AI Source: %s (Gemini Configured: %s)" % (ai_res["source"], ai_res["gemini_configured"]))
        print(" [OK] Analysis: %s" % ai_res["analysis"][:120] + "...")
        print(" [OK] Observed Facts Count: %d | Causes: %d | Actions: %d" % (
            len(ai_res["observed_facts"]), len(ai_res["possible_causes"]), len(ai_res["recommended_actions"])
        ))
        assert len(ai_res["observed_facts"]) > 0

        # Test GET /api/insights/summary
        print("\nTesting GET /api/insights/summary...")
        code, ai_sum = make_request("http://127.0.0.1:8000/api/insights/summary")
        assert code == 200
        print(" [OK] Headline: %s" % ai_sum["headline"])
        print(" [OK] Health Level: %s" % ai_sum["health_level"])
        print(" [OK] Key Recommendation: %s" % ai_sum["key_recommendation"])

        # 3. Frontend Static Build Verification
        print("\n--- 3. VERIFYING DAY 3 REACT FRONTEND SERVING ---")
        code, dash_html = make_request("http://127.0.0.1:8000/dashboard")
        assert code == 200
        assert '<div id="root">' in dash_html
        print(" [OK] GET /dashboard -> 200 OK (Rendered React dist HTML with root element)")

        # Verify asset references
        assert "/assets/index-" in dash_html
        print(" [OK] Frontend JavaScript & Tailwind CSS asset bundles verified in HTML markup")

        # 4. WebSocket Streaming Verification
        print("\n--- 4. VERIFYING REAL-TIME WEBSOCKET STREAMING ---")
        ws_ok = asyncio.run(test_websocket_stream("ws://127.0.0.1:8000/ws/metrics"))
        assert ws_ok is True

        print("\n" + "=" * 75)
        print("ALL DAY 1, DAY 2, AND DAY 3 FUNCTIONALITY VERIFIED WITH 100% SUCCESS!")
        print("=" * 75)

    finally:
        print("\nTerminating live server process...")
        server_process.terminate()
        server_process.wait(timeout=5)
        print("Server shutdown complete.")


if __name__ == "__main__":
    run_day3_verification()
