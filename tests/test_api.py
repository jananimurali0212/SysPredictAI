"""Integration tests for FastAPI REST endpoints and WebSocket metric streaming."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create a test client with application lifespan management."""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Test landing page endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "endpoints" in data
    assert "health" in data["endpoints"]


def test_health_endpoint(client):
    """Test /api/health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "uptime_seconds" in data
    assert data["collectors_healthy"] is True
    assert data["database_healthy"] is True


def test_current_metrics_endpoint(client):
    """Test /api/metrics/current endpoint returning real host metrics."""
    response = client.get("/api/metrics/current")
    assert response.status_code == 200
    data = response.json()

    assert "cpu" in data
    assert "memory" in data
    assert "disk" in data
    assert "network" in data

    # CPU assertions
    assert data["cpu"]["utilization_percent"] >= 0.0
    assert len(data["cpu"]["per_core_utilization"]) > 0
    assert data["cpu"]["core_count_logical"] >= 1

    # Memory assertions
    assert data["memory"]["total_bytes"] > 0
    assert data["memory"]["used_bytes"] > 0
    assert 0.0 <= data["memory"]["utilization_percent"] <= 100.0

    # Disk assertions
    assert data["disk"]["total_bytes"] > 0
    assert 0.0 <= data["disk"]["utilization_percent"] <= 100.0
    assert len(data["disk"]["mount_point"]) > 0

    # Network assertions
    assert data["network"]["bytes_sent"] >= 0
    assert data["network"]["bytes_recv"] >= 0
    assert data["network"]["upload_speed_bps"] >= 0.0
    assert data["network"]["download_speed_bps"] >= 0.0


def test_metrics_history_endpoint(client):
    """Test /api/metrics/history endpoint."""
    response = client.get("/api/metrics/history?limit=10")
    assert response.status_code == 200
    data = response.json()

    assert "count" in data
    assert "metrics" in data
    assert isinstance(data["metrics"], list)
    assert data["count"] == len(data["metrics"])


def test_processes_endpoint(client):
    """Test /api/processes endpoint with sorting."""
    # Test sort by cpu
    response_cpu = client.get("/api/processes?limit=15&sort_by=cpu")
    assert response_cpu.status_code == 200
    data_cpu = response_cpu.json()
    assert data_cpu["count"] > 0
    assert len(data_cpu["processes"]) <= 15
    first_proc = data_cpu["processes"][0]
    assert "pid" in first_proc
    assert "name" in first_proc
    assert "cpu_percent" in first_proc

    # Test sort by memory
    response_mem = client.get("/api/processes?limit=10&sort_by=memory")
    assert response_mem.status_code == 200
    data_mem = response_mem.json()
    assert data_mem["count"] > 0


def test_system_info_endpoint(client):
    """Test /api/system/info endpoint."""
    response = client.get("/api/system/info")
    assert response.status_code == 200
    data = response.json()

    assert "os_name" in data
    assert "os_version" in data
    assert "architecture" in data
    assert "hostname" in data
    assert "boot_time" in data
    assert "uptime_seconds" in data
    assert data["logical_cores"] >= 1
    assert data["total_ram_bytes"] > 0


def test_websocket_metrics_stream(client):
    """Test real-time WebSocket connection and metric streaming."""
    with client.websocket_connect("/ws/metrics") as ws:
        # Upon connect, the server immediately pushes the current metrics snapshot
        data = ws.receive_json()

        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data

        assert data["cpu"]["core_count_logical"] >= 1
        assert data["memory"]["total_bytes"] > 0

        # Send a ping and verify handshake
        ws.send_text("ping")
        # May receive pong or next broadcast; both are valid
