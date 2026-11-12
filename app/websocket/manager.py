"""WebSocket connection manager for real-time telemetry streaming."""
import asyncio
import logging
from typing import Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and handles broadcasts."""

    def __init__(self):
        self._active_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register an incoming WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._active_connections.add(websocket)
            logger.info("WebSocket client connected. Active connections: %d", len(self._active_connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a closed or dropped WebSocket connection."""
        async with self._lock:
            self._active_connections.discard(websocket)
            logger.info("WebSocket client disconnected. Active connections: %d", len(self._active_connections))

    async def broadcast_json(self, data: dict) -> None:
        """Broadcast JSON payload to all active WebSocket connections, cleaning up dead sockets."""
        async with self._lock:
            connections = list(self._active_connections)

        if not connections:
            return

        dead_connections = []
        for ws in connections:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.debug("Failed to send message to client, marking for removal: %s", e)
                dead_connections.append(ws)

        if dead_connections:
            async with self._lock:
                for ws in dead_connections:
                    self._active_connections.discard(ws)

    @property
    def client_count(self) -> int:
        """Return the current number of active connections."""
        return len(self._active_connections)


_connection_manager_instance = None


def get_connection_manager() -> ConnectionManager:
    """Singleton getter for the global ConnectionManager."""
    global _connection_manager_instance
    if _connection_manager_instance is None:
        _connection_manager_instance = ConnectionManager()
    return _connection_manager_instance

