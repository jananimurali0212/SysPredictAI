"""Comprehensive live server end-to-end verification script."""
import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.request
import websockets


def make_request(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "VerificationScript/1.0"})
    with urllib.request.urlopen(req, timeout=5) as response:
        return response.getcode(), json.loads(response.read().decode("utf-8"))


async def test_websocket_stream(ws_url: str):
    print("Testing WebSocket streaming from %s..." % ws_url)
    async with websockets.connect(ws_url) as ws:
        msg1 = await asyncio.wait_for(ws.recv(), timeout=5.0)
        data1 = json.loads(msg1)
        print(" -> Received WS Message 1: CPU=%.1f%%, RAM=%.1f%%, Disk=%.1f%%, Upload=%.1f B/s, Download=%.1f B/s" % (
            data1["cpu"]["utilization_percent"],
            data1["memory"]["utilization_percent"],
            data1["disk"]["utilization_percent"],
            data1["network"]["upload_speed_bps"],
            data1["network"]["download_speed_bps"],
        ))

        msg2 = await asyncio.wait_for(ws.recv(), timeout=5.0)
        data2 = json.loads(msg2)
        print(" -> Received WS Message 2: CPU=%.1f%%, RAM=%.1f%%, Disk=%.1f%%, Upload=%.1f B/s, Download=%.1f B/s" % (
            data2["cpu"]["utilization_percent"],
            data2["memory"]["utilization_percent"],
            data2["disk"]["utilization_percent"],
            data2["network"]["upload_speed_bps"],
            data2["network"]["download_speed_bps"],
        ))
        assert "cpu" in data2 and "memory" in data2 and "disk" in data2 and "network" in data2
        return True


def run_verification():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    python_exe = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
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

    print("=" * 70)
    print("STARTING LIVE FASTAPI SERVER ON 127.0.0.1:8000...")
    print("=" * 70)

    server_process = subprocess.Popen(server_cmd, cwd=base_dir)

    try:
        # Wait up to 10 seconds for server to be responsive
        server_ready = False
        for attempt in range(20):
            try:
                code, data = make_request("http://127.0.0.1:8000/api/health")
                if code == 200:
                    server_ready = True
                    break
            except Exception:
                time.sleep(0.5)

        if not server_ready:
            raise RuntimeError("FastAPI server failed to start within timeout.")

        print("[OK] FastAPI server is live and responsive!\n")

        # 1. Verify health endpoint
        print("1. Verifying GET /api/health:")
        code, health = make_request("http://127.0.0.1:8000/api/health")
        print("   Status Code: %d" % code)
        print("   Payload: %s" % json.dumps(health, indent=2))
        assert health["status"] == "healthy"
        assert health["collectors_healthy"] is True
        assert health["database_healthy"] is True

        # 2. Verify current metrics (CPU, RAM, Disk, Network)
        print("\n2. Verifying GET /api/metrics/current:")
        code, current = make_request("http://127.0.0.1:8000/api/metrics/current")
        print("   Status Code: %d" % code)
        print("   CPU: overall=%.1f%%, physical_cores=%s, logical_cores=%d, freq=%s MHz" % (
            current["cpu"]["utilization_percent"],
            current["cpu"]["core_count_physical"],
            current["cpu"]["core_count_logical"],
            current["cpu"]["frequency"]["current"] if current["cpu"]["frequency"] else "N/A"
        ))
        print("   Per-core CPU: %s" % current["cpu"]["per_core_utilization"])
        print("   Memory: total=%.2f GB, used=%.2f GB, percent=%.1f%%" % (
            current["memory"]["total_bytes"] / (1024**3),
            current["memory"]["used_bytes"] / (1024**3),
            current["memory"]["utilization_percent"],
        ))
        print("   Disk: mount=%s, total=%.2f GB, used=%.2f GB, percent=%.1f%%" % (
            current["disk"]["mount_point"],
            current["disk"]["total_bytes"] / (1024**3),
            current["disk"]["used_bytes"] / (1024**3),
            current["disk"]["utilization_percent"],
        ))
        print("   Network: sent=%d bytes, recv=%d bytes, upload=%.1f B/s, download=%.1f B/s" % (
            current["network"]["bytes_sent"],
            current["network"]["bytes_recv"],
            current["network"]["upload_speed_bps"],
            current["network"]["download_speed_bps"],
        ))

        # 3. Verify network speed calculation over time interval
        print("\n3. Waiting 1.5 seconds to measure network speed update...")
        time.sleep(1.5)
        _, current2 = make_request("http://127.0.0.1:8000/api/metrics/current")
        print("   Updated Network Speeds: upload=%.2f B/s, download=%.2f B/s" % (
            current2["network"]["upload_speed_bps"],
            current2["network"]["download_speed_bps"],
        ))

        # 4. Verify process table
        print("\n4. Verifying GET /api/processes?limit=5&sort_by=cpu:")
        code, procs = make_request("http://127.0.0.1:8000/api/processes?limit=5&sort_by=cpu")
        print("   Status Code: %d, Total returned: %d" % (code, procs["count"]))
        for p in procs["processes"]:
            print("   -> PID %6d | %-25s | CPU %5.1f%% | RAM %5.1f%% | %10d bytes | Status: %s" % (
                p["pid"], p["name"][:25], p["cpu_percent"], p["memory_percent"], p["memory_rss_bytes"], p["status"]
            ))

        # 5. Verify system specifications info
        print("\n5. Verifying GET /api/system/info:")
        code, sys_info = make_request("http://127.0.0.1:8000/api/system/info")
        print("   Status Code: %d" % code)
        print("   OS: %s %s (%s)" % (sys_info["os_name"], sys_info["os_version"], sys_info["architecture"]))
        print("   Hostname: %s" % sys_info["hostname"])
        print("   CPU Model: %s" % sys_info["cpu_model"])
        print("   Cores: %s physical, %d logical" % (sys_info["physical_cores"], sys_info["logical_cores"]))
        print("   Total RAM: %.2f GB" % (sys_info["total_ram_bytes"] / (1024**3)))
        print("   Uptime: %.1f seconds" % sys_info["uptime_seconds"])

        # 6. Verify SQLite historical metric persistence
        print("\n6. Verifying GET /api/metrics/history?limit=5:")
        code, history = make_request("http://127.0.0.1:8000/api/metrics/history?limit=5")
        print("   Status Code: %d, Historical records saved: %d" % (code, history["count"]))
        assert history["count"] > 0
        latest_record = history["metrics"][0]
        print("   Latest record ID: %s, Timestamp: %s, CPU: %.1f%%" % (
            latest_record["id"], latest_record["timestamp"], latest_record["cpu"]["utilization_percent"]
        ))

        # 7. Verify WebSocket real-time streaming
        print("\n7. Verifying WebSocket /ws/metrics:")
        ws_success = asyncio.run(test_websocket_stream("ws://127.0.0.1:8000/ws/metrics"))
        assert ws_success is True

        print("\n" + "=" * 70)
        print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY WITH ZERO ERRORS!")
        print("=" * 70)

    finally:
        print("\nTerminating live server process...")
        server_process.terminate()
        server_process.wait(timeout=5)
        print("Server shutdown complete.")


if __name__ == "__main__":
    run_verification()

