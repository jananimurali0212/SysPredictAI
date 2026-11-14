"""Automated tests for Gemini AI Insights and grounded diagnostic telemetry reasoning."""
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.ai import AIInsightResponse, AISummaryResponse
from app.schemas.metrics import (
    CPUMetrics,
    DiskMetrics,
    MemoryMetrics,
    NetworkMetrics,
    ProcessMetric,
    SystemMetricsSnapshot,
)
from app.services.ai_service import AIService


@pytest.fixture(scope="module")
def client():
    """Create a test client with application lifespan management."""
    with TestClient(app) as test_client:
        yield test_client


def make_test_snapshot(cpu: float = 85.0, mem: float = 88.0) -> SystemMetricsSnapshot:
    """Construct controlled snapshot for diagnostic tests."""
    return SystemMetricsSnapshot(
        timestamp=datetime.now(timezone.utc),
        cpu=CPUMetrics(
            utilization_percent=cpu,
            per_core_utilization=[cpu, cpu],
            core_count_physical=4,
            core_count_logical=8,
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
            used_bytes=300000000000,
            available_bytes=200000000000,
            utilization_percent=60.0,
        ),
        network=NetworkMetrics(
            bytes_sent=1000000,
            bytes_recv=2000000,
            upload_speed_bps=5000.0,
            download_speed_bps=10000.0,
        ),
    )


def test_ai_service_initialization():
    """Verify AIService initializes safely with or without GEMINI_API_KEY."""
    ai = AIService(api_key=None)
    assert ai.is_configured() is False


@pytest.mark.asyncio
async def test_ai_service_local_reasoning_cpu():
    """Verify grounded CPU diagnostics distinguish observed facts from causes and actions."""
    ai = AIService(api_key=None)
    snap = make_test_snapshot(cpu=88.5, mem=45.0)
    top_procs = [
        ProcessMetric(
            pid=1234,
            name="ffmpeg.exe",
            cpu_percent=65.2,
            memory_percent=12.1,
            memory_rss_bytes=100000000,
            status="running",
            create_time=None,
            username=None,
        )
    ]

    res = await ai.answer_question(
        question="Why is my CPU usage high?",
        current_metrics=snap,
        top_processes=top_procs,
        anomalies=[],
        risk_resp=None,
        cpu_prediction=None,
    )

    assert isinstance(res, AIInsightResponse)
    assert res.source == "grounded_telemetry_engine"
    assert "88.5" in res.analysis or "CPU" in res.analysis
    assert len(res.observed_facts) > 0
    assert len(res.possible_causes) > 0
    assert len(res.recommended_actions) > 0
    assert any("ffmpeg.exe" in f for f in res.observed_facts)


@pytest.mark.asyncio
async def test_ai_service_local_reasoning_memory():
    """Verify grounded memory diagnostics respond to RAM questions."""
    ai = AIService(api_key=None)
    snap = make_test_snapshot(cpu=15.0, mem=91.0)
    res = await ai.answer_question(
        question="Why is my RAM utilization increasing?",
        current_metrics=snap,
        top_processes=[],
        anomalies=[],
        risk_resp=None,
        cpu_prediction=None,
    )
    assert isinstance(res, AIInsightResponse)
    assert "RAM" in res.analysis or "memory" in res.analysis
    assert len(res.recommended_actions) > 0


def test_ai_service_summary():
    """Verify executive summary generation for dashboard overview."""
    ai = AIService(api_key=None)
    snap = make_test_snapshot(cpu=92.0, mem=93.0)
    summary = ai.generate_system_summary(
        current_metrics=snap,
        anomalies=[],
        risk_resp=None,
    )
    assert isinstance(summary, AISummaryResponse)
    assert summary.health_level == "critical"
    assert len(summary.headline) > 0
    assert len(summary.key_recommendation) > 0


def test_api_insights_query_endpoint(client):
    """Test POST /api/insights/query endpoint."""
    payload = {"question": "What is the current system health?"}
    response = client.post("/api/insights/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["question"] == payload["question"]
    assert "analysis" in data
    assert "observed_facts" in data
    assert isinstance(data["observed_facts"], list)
    assert "possible_causes" in data
    assert isinstance(data["possible_causes"], list)
    assert "recommended_actions" in data
    assert isinstance(data["recommended_actions"], list)


def test_api_insights_summary_endpoint(client):
    """Test GET /api/insights/summary endpoint."""
    response = client.get("/api/insights/summary")
    assert response.status_code == 200
    data = response.json()
    assert "headline" in data
    assert "summary" in data
    assert data["health_level"] in ["healthy", "warning", "critical"]
    assert "key_recommendation" in data
