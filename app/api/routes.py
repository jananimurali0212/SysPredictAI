"""FastAPI route handlers for telemetry REST endpoints and WebSocket stream."""
import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.schemas.metrics import (
    HealthResponse,
    HistoricalMetricsResponse,
    ProcessListResponse,
    SystemInfo,
    SystemMetricsSnapshot,
)
from app.services.monitoring_service import MonitoringService, get_monitoring_service
from app.websocket.manager import ConnectionManager, get_connection_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Monitoring"])
ws_router = APIRouter(tags=["WebSocket"])


@router.get("/health", response_model=HealthResponse, summary="Service health status")
async def health_check(
    service: MonitoringService = Depends(get_monitoring_service),
) -> HealthResponse:
    """Check availability of system collectors and SQLite database."""
    return service.get_health()


@router.get("/metrics/current", response_model=SystemMetricsSnapshot, summary="Current system metrics")
async def get_current_metrics(
    service: MonitoringService = Depends(get_monitoring_service),
) -> SystemMetricsSnapshot:
    """Get the latest real hardware metrics for CPU, RAM, Disk, and Network."""
    return service.get_current_metrics()


@router.get("/metrics/history", response_model=HistoricalMetricsResponse, summary="Historical metrics")
async def get_metrics_history(
    limit: int = Query(default=100, ge=1, le=1000, description="Max snapshots to retrieve"),
    start_time: Optional[datetime] = Query(default=None, description="Filter records starting from UTC timestamp"),
    end_time: Optional[datetime] = Query(default=None, description="Filter records up to UTC timestamp"),
    service: MonitoringService = Depends(get_monitoring_service),
) -> HistoricalMetricsResponse:
    """Query persisted historical system metric snapshots."""
    return service.get_history(limit=limit, start_time=start_time, end_time=end_time)


@router.get("/processes", response_model=ProcessListResponse, summary="Active process table")
async def get_processes(
    limit: int = Query(default=50, ge=1, le=500, description="Maximum number of processes to return"),
    sort_by: str = Query(default="cpu", pattern="^(cpu|memory)$", description="Sort attribute ('cpu' or 'memory')"),
    service: MonitoringService = Depends(get_monitoring_service),
) -> ProcessListResponse:
    """List running processes with CPU and memory usage, handling access-denied safely."""
    return service.get_processes(limit=limit, sort_by=sort_by)


@router.get("/system/info", response_model=SystemInfo, summary="Host machine specifications")
async def get_system_info(
    service: MonitoringService = Depends(get_monitoring_service),
) -> SystemInfo:
    """Retrieve host machine platform, CPU cores, memory size, and boot time."""
    return service.get_system_info()


@ws_router.websocket("/ws/metrics")
async def websocket_metrics_stream(
    websocket: WebSocket,
    service: MonitoringService = Depends(get_monitoring_service),
    manager: ConnectionManager = Depends(get_connection_manager),
):
    """Real-time WebSocket stream delivering updated system metrics at 1-second cadence."""
    await manager.connect(websocket)

    # Immediately push the latest current metrics snapshot on connect
    try:
        current_snapshot = service.get_current_metrics()
        await websocket.send_json(current_snapshot.model_dump(mode="json"))
    except Exception as e:
        logger.debug("Failed to deliver initial snapshot to WebSocket client: %s", e)

    try:
        # Keep connection open and handle optional client pings
        while True:
            # Client messages (such as ping/pong or settings)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                # Echo or handle client heartbeat if needed
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Idle timeout keepalive: verify socket is still healthy
                continue
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.warning("WebSocket stream encountered error: %s", e)
        await manager.disconnect(websocket)

