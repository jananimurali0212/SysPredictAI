"""SQLite database manager for persistent metrics logging."""
import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator, List, Optional

import pandas as pd

from app.config import settings
from app.database.models import CREATE_METRICS_TABLE_SQL, CREATE_TIMESTAMP_INDEX_SQL, METRICS_TABLE_NAME
from app.schemas.metrics import SystemMetricsSnapshot

logger = logging.getLogger(__name__)


class Database:
    """Manages SQLite storage for historical system metrics."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self._lock = threading.Lock()
        self._initialized = False

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provide a context-managed SQLite connection with WAL enabled."""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_db(self) -> None:
        """Initialize tables and indexes safely, avoiding duplicate initialization."""
        with self._lock:
            if self._initialized:
                return

            with self.get_connection() as conn:
                cursor = conn.cursor()
                if settings.DB_PRAGMA_WAL:
                    cursor.execute("PRAGMA journal_mode=WAL;")
                    cursor.execute("PRAGMA synchronous=NORMAL;")
                cursor.execute(CREATE_METRICS_TABLE_SQL)
                cursor.execute(CREATE_TIMESTAMP_INDEX_SQL)
                conn.commit()

            self._initialized = True
            logger.info("Initialized SQLite metrics database at %s", self.db_path)

    def save_metric(self, snapshot: SystemMetricsSnapshot) -> int:
        """Persist a system metrics snapshot to SQLite."""
        self.init_db()

        raw_json = snapshot.model_dump_json()
        ts_str = snapshot.timestamp.isoformat()

        insert_sql = f"""
        INSERT INTO {METRICS_TABLE_NAME} (
            timestamp,
            cpu_percent,
            cpu_cores_logical,
            memory_percent,
            memory_used_bytes,
            memory_total_bytes,
            disk_percent,
            disk_used_bytes,
            disk_total_bytes,
            bytes_sent,
            bytes_recv,
            upload_speed_bps,
            download_speed_bps,
            raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        params = (
            ts_str,
            snapshot.cpu.utilization_percent,
            snapshot.cpu.core_count_logical,
            snapshot.memory.utilization_percent,
            snapshot.memory.used_bytes,
            snapshot.memory.total_bytes,
            snapshot.disk.utilization_percent,
            snapshot.disk.used_bytes,
            snapshot.disk.total_bytes,
            snapshot.network.bytes_sent,
            snapshot.network.bytes_recv,
            snapshot.network.upload_speed_bps,
            snapshot.network.download_speed_bps,
            raw_json,
        )

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(insert_sql, params)
            conn.commit()
            return cursor.lastrowid

    def get_history(
        self,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[SystemMetricsSnapshot]:
        """Fetch historical snapshots ordered chronologically (newest first)."""
        self.init_db()

        query = f"SELECT id, raw_json FROM {METRICS_TABLE_NAME}"
        conditions = []
        params = []

        if start_time is not None:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time is not None:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(max(1, limit))

        snapshots: List[SystemMetricsSnapshot] = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                try:
                    data = json.loads(row["raw_json"])
                    data["id"] = row["id"]
                    snapshot = SystemMetricsSnapshot.model_validate(data)
                    snapshots.append(snapshot)
                except Exception as e:
                    logger.warning("Error deserializing historical metric id=%s: %s", row["id"], e)

        return snapshots

    def get_history_df(
        self,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Fetch historical telemetry directly into a Pandas DataFrame."""
        self.init_db()

        query = f"""
        SELECT
            id,
            timestamp,
            cpu_percent,
            cpu_cores_logical,
            memory_percent,
            memory_used_bytes,
            memory_total_bytes,
            disk_percent,
            disk_used_bytes,
            disk_total_bytes,
            bytes_sent,
            bytes_recv,
            upload_speed_bps,
            download_speed_bps
        FROM {METRICS_TABLE_NAME}
        """
        conditions = []
        params = []

        if start_time is not None:
            conditions.append("timestamp >= ?")
            params.append(start_time.isoformat())
        if end_time is not None:
            conditions.append("timestamp <= ?")
            params.append(end_time.isoformat())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(max(1, limit))

        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            if not df.empty and "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            return df

    def cleanup_old_metrics(self, hours: int = 24) -> int:
        """Prune records older than the specified retention window."""
        self.init_db()
        cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        cutoff_iso = datetime.fromtimestamp(cutoff, tz=timezone.utc).isoformat()

        sql = f"DELETE FROM {METRICS_TABLE_NAME} WHERE timestamp < ?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (cutoff_iso,))
            conn.commit()
            deleted = cursor.rowcount
            if deleted > 0:
                logger.info("Pruned %d expired metric records", deleted)
            return deleted

    def is_healthy(self) -> bool:
        """Verify that the SQLite database is reachable and responsive."""
        try:
            self.init_db()
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1;")
                row = cursor.fetchone()
                return bool(row and row[0] == 1)
        except Exception as e:
            logger.error("Database health check failed: %s", e)
            return False


# Singleton database instance
_db_instance: Optional[Database] = None


def get_db() -> Database:
    """Retrieve or construct the application database singleton."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance

