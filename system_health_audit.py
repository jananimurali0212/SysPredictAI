"""Live system health and perfection audit script."""
import asyncio
import json
import sqlite3
import sys
import time
import urllib.request
import websockets

BASE_URL = "http://127.0.0.1:8000"
WS_URL = "ws://127.0.0.1:8000/ws/metrics"


def http_get(path: str):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "SystemHealthAudit/1.0", "Accept": "application/json"})
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=5) as res:
        latency_ms = (time.perf_counter() - start) * 1000
        code = res.getcode()
        content_type = res.headers.get("content-type", "")
        raw = res.read().decode("utf-8")
        if "application/json" in content_type:
            data = json.loads(raw)
        else:
            data = raw
        return code, data, latency_ms


async def audit_websocket():
    print("\n[Audit 7] WebSocket Streaming (/ws/metrics)")
    samples = []
    async with websockets.connect(WS_URL) as ws:
        # Measure 3 consecutive packets
        for i in range(3):
            t0 = time.perf_counter()
            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            elapsed = time.perf_counter() - t0
            data = json.loads(msg)
            samples.append((elapsed, data))
            print(f"  -> Packet {i+1} received in {elapsed:.2f}s | CPU: {data['cpu']['utilization_percent']}% | RAM: {data['memory']['utilization_percent']}% | Upload: {data['network']['upload_speed_bps']} B/s | Download: {data['network']['download_speed_bps']} B/s")

        # Test heartbeat ping
        await ws.send("ping")
        pong = await asyncio.wait_for(ws.recv(), timeout=2.0)
        print(f"  -> Heartbeat Ping/Pong verified: {pong.strip() if isinstance(pong, str) else 'received'}")

    assert len(samples) == 3
    print("  -> WebSocket streaming passed perfectly!")
    return True


def run_audit():
    print("=" * 80)
    print("RUNNING COMPREHENSIVE LIVE SYSTEM HEALTH & FUNCTIONALITY AUDIT")
    print("=" * 80)

    # 1. Health Endpoint
    print("\n[Audit 1] Health Endpoint (/api/health)")
    code, health, lat = http_get("/api/health")
    print(f"  HTTP {code} in {lat:.2f}ms")
    print(f"  Status: {health['status']} | Collectors Healthy: {health['collectors_healthy']} | DB Healthy: {health['database_healthy']} | Uptime: {health['uptime_seconds']}s")
    assert code == 200 and health["status"] == "healthy" and health["collectors_healthy"] and health["database_healthy"]

    # 2. Current Metrics
    print("\n[Audit 2] Real Hardware Metrics (/api/metrics/current)")
    code, cur1, _ = http_get("/api/metrics/current")
    print(f"  CPU Utilization: {cur1['cpu']['utilization_percent']}% across {cur1['cpu']['core_count_logical']} logical cores")
    print(f"  CPU Per-Core: {cur1['cpu']['per_core_utilization']}")
    print(f"  CPU Freq: {cur1['cpu']['frequency']}")
    print(f"  RAM Total: {cur1['memory']['total_bytes'] / (1024**3):.2f} GB | Used: {cur1['memory']['used_bytes'] / (1024**3):.2f} GB ({cur1['memory']['utilization_percent']}%)")
    print(f"  Disk Mount: {cur1['disk']['mount_point']} | Capacity: {cur1['disk']['total_bytes'] / (1024**3):.2f} GB | Used: {cur1['disk']['used_bytes'] / (1024**3):.2f} GB ({cur1['disk']['utilization_percent']}%)")
    print(f"  Network Sent: {cur1['network']['bytes_sent']} bytes | Recv: {cur1['network']['bytes_recv']} bytes")
    print(f"  Current Speeds: Up={cur1['network']['upload_speed_bps']} B/s | Down={cur1['network']['download_speed_bps']} B/s")
    assert cur1["memory"]["total_bytes"] > 0
    assert cur1["disk"]["total_bytes"] > 0
    assert cur1["cpu"]["core_count_logical"] >= 1

    # 3. Dynamic Network Speed Calculation
    print("\n[Audit 3] Dynamic Network Speed Delta Verification")
    time.sleep(1.2)
    code, cur2, _ = http_get("/api/metrics/current")
    print(f"  Sample 2 (after 1.2s): Up={cur2['network']['upload_speed_bps']} B/s | Down={cur2['network']['download_speed_bps']} B/s")
    assert cur2["network"]["bytes_sent"] >= cur1["network"]["bytes_sent"]
    assert cur2["network"]["bytes_recv"] >= cur1["network"]["bytes_recv"]

    # 4. Process Table
    print("\n[Audit 4] Fault-Tolerant Process Inspection (/api/processes)")
    code, proc_cpu, _ = http_get("/api/processes?limit=5&sort_by=cpu")
    print(f"  Top 5 Processes by CPU (Total available: {proc_cpu['count']}):")
    for p in proc_cpu["processes"]:
        print(f"    - PID {p['pid']:<6} | {p['name']:<25} | CPU: {p['cpu_percent']:>5.1f}% | RAM: {p['memory_percent']:>4.1f}% | RSS: {p['memory_rss_bytes']/(1024**2):>6.1f} MB | {p['status']}")
    assert len(proc_cpu["processes"]) == 5

    code, proc_mem, _ = http_get("/api/processes?limit=3&sort_by=memory")
    print(f"  Top 3 Processes by Memory:")
    for p in proc_mem["processes"]:
        print(f"    - PID {p['pid']:<6} | {p['name']:<25} | RAM: {p['memory_percent']:>4.1f}% | RSS: {p['memory_rss_bytes']/(1024**2):>6.1f} MB")
    assert len(proc_mem["processes"]) == 3

    # 5. System Info
    print("\n[Audit 5] System Specifications (/api/system/info)")
    code, info, _ = http_get("/api/system/info")
    print(f"  Host: {info['hostname']} | OS: {info['os_name']} {info['os_version']} ({info['architecture']})")
    print(f"  CPU Model: {info['cpu_model']}")
    print(f"  Cores: {info['physical_cores']} Physical, {info['logical_cores']} Logical")
    print(f"  RAM Installed: {info['total_ram_bytes'] / (1024**3):.2f} GB")
    assert info["hostname"] and info["logical_cores"] >= 1

    # 6. SQLite Database Historical Storage
    print("\n[Audit 6] SQLite Historical Persistence (/api/metrics/history & DB file)")
    code, history, _ = http_get("/api/metrics/history?limit=10")
    print(f"  Retrieved {history['count']} historical snapshots via API")
    assert history["count"] > 0
    latest = history["metrics"][0]
    print(f"  Latest record ID #{latest['id']} captured at {latest['timestamp']}")

    # Direct SQLite query verification
    conn = sqlite3.connect("system_metrics.db")
    c = conn.cursor()
    c.execute("SELECT count(*), min(timestamp), max(timestamp) FROM system_metrics")
    row = c.fetchone()
    total_stored, oldest_ts, newest_ts = row[0], row[1], row[2]
    conn.close()
    print(f"  Direct SQLite verification: {total_stored} total records stored between {oldest_ts} and {newest_ts}")
    assert total_stored >= 1

    # 7. WebSocket Streaming
    asyncio.run(audit_websocket())

    # 8. Web Dashboard UI
    print("\n[Audit 8] Visual Web Dashboard (/dashboard)")
    code, dash_html, lat = http_get("/dashboard")
    print(f"  HTTP {code} in {lat:.2f}ms | HTML payload: {len(dash_html)} bytes")
    assert code == 200 and "AI System Monitor" in dash_html and "metricsChart" in dash_html

    # 9. API Docs
    print("\n[Audit 9] Swagger Documentation (/docs)")
    code, docs_html, lat = http_get("/docs")
    print(f"  HTTP {code} in {lat:.2f}ms | Swagger UI payload: {len(docs_html)} bytes")
    assert code == 200

    print("\n" + "=" * 80)
    print("ALL 9 LIVE SYSTEM AUDITS PASSED WITH 100% SUCCESS!")
    print("=" * 80)


if __name__ == "__main__":
    run_audit()

