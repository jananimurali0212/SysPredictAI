"""Database schema definitions and constants for SQLite metrics storage."""

METRICS_TABLE_NAME = "system_metrics"

CREATE_METRICS_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {METRICS_TABLE_NAME} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    cpu_percent REAL NOT NULL,
    cpu_cores_logical INTEGER NOT NULL,
    memory_percent REAL NOT NULL,
    memory_used_bytes INTEGER NOT NULL,
    memory_total_bytes INTEGER NOT NULL,
    disk_percent REAL NOT NULL,
    disk_used_bytes INTEGER NOT NULL,
    disk_total_bytes INTEGER NOT NULL,
    bytes_sent INTEGER NOT NULL,
    bytes_recv INTEGER NOT NULL,
    upload_speed_bps REAL NOT NULL,
    download_speed_bps REAL NOT NULL,
    raw_json TEXT NOT NULL
);
"""

CREATE_TIMESTAMP_INDEX_SQL = f"""
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON {METRICS_TABLE_NAME} (timestamp DESC);
"""

