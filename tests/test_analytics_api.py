"""Integration tests for predictive analytics and anomaly detection REST API endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create a test client with application lifespan management."""
    with TestClient(app) as test_client:
        yield test_client


def test_api_predictions_cpu_endpoint(client):
    """Test GET /api/predictions/cpu returns structured prediction response."""
    response = client.get("/api/predictions/cpu")
    assert response.status_code == 200
    data = response.json()

    assert data["metric"] == "cpu"
    assert data["status"] in ["success", "insufficient_data"]
    assert "timestamp" in data
    assert "method_used" in data
    assert isinstance(data["predictions"], list)


def test_api_predictions_cpu_with_horizons(client):
    """Test GET /api/predictions/cpu with custom horizons query parameter."""
    response = client.get("/api/predictions/cpu?horizons=30,60,180")
    assert response.status_code == 200
    data = response.json()
    assert data["metric"] == "cpu"


def test_api_predictions_memory_endpoint(client):
    """Test GET /api/predictions/memory returns structured prediction response."""
    response = client.get("/api/predictions/memory")
    assert response.status_code == 200
    data = response.json()

    assert data["metric"] == "memory"
    assert data["status"] in ["success", "insufficient_data"]
    assert "timestamp" in data
    assert "method_used" in data
    assert isinstance(data["predictions"], list)


def test_api_predictions_summary_endpoint(client):
    """Test GET /api/predictions/summary returns synthesized executive forecast."""
    response = client.get("/api/predictions/summary")
    assert response.status_code == 200
    data = response.json()

    assert "cpu_forecast" in data
    assert "memory_forecast" in data
    assert "summary" in data
    assert len(data["summary"]) > 0


def test_api_anomalies_endpoint(client):
    """Test GET /api/anomalies returns structured anomaly list."""
    response = client.get("/api/anomalies")
    assert response.status_code == 200
    data = response.json()

    assert "total_anomalies" in data
    assert "isolation_forest_enabled" in data
    assert "anomalies" in data
    assert isinstance(data["anomalies"], list)

    for anom in data["anomalies"]:
        assert "anomaly_id" in anom
        assert "metric_name" in anom
        assert "observed_value" in anom
        assert "severity" in anom
        assert anom["severity"] in ["Low", "Medium", "High", "Critical"]
        assert "explanation" in anom
        assert "recommended_action" in anom


def test_api_risk_endpoint(client):
    """Test GET /api/risk returns holistic risk assessment."""
    response = client.get("/api/risk")
    assert response.status_code == 200
    data = response.json()

    assert "risk_status" in data
    assert data["risk_status"] in ["Normal", "Warning", "High Risk", "Critical"]
    assert 0.0 <= data["risk_score"] <= 100.0
    assert "current_cpu_percent" in data
    assert "current_memory_percent" in data
    assert "breakdown" in data
    assert "cpu_status" in data["breakdown"]
    assert "memory_status" in data["breakdown"]
    assert "disk_status" in data["breakdown"]
    assert "network_status" in data["breakdown"]
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)

