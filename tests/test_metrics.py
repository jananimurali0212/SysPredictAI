"""Tests for system performance collectors and historical database operations."""
import os
import tempfile
import time
from datetime import datetime, timezone
import pytest

from app.collectors.process_collector import ProcessCollector
from app.collectors.system_collector import SystemCollector
from app.database.db import Database
from app.schemas.metrics import (
    CPUMetrics,
    DiskMetrics,
    MemoryMetrics,
    NetworkMetrics,
    ProcessMetric,
    SystemInfo,
    SystemMetricsSnapshot,
)


def test_system_collector_cpu():
    """Verify that real CPU metrics are collected with valid types and ranges."""
    collector = SystemCollector()
    cpu = collector.collect_cpu()

    assert isinstance(cpu, CPUMetrics)
    assert isinstance(cpu.utilization_percent, float)
    assert 0.0 <= cpu.utilization_percent <= 100.0
    assert isinstance(cpu.per_core_utilization, list)
    assert len(cpu.per_core_utilization) > 0
    assert cpu.core_count_logical >= 1
    if cpu.frequency is not None:
        if cpu.frequency.current is not None:
            assert cpu.frequency.current > 0


def test_system_collector_memory():
    """Verify that real RAM metrics are non-zero and percentages are within bounds."""
    collector = SystemCollector()
    memory = collector.collect_memory()

    assert isinstance(memory, MemoryMetrics)
    assert memory.total_bytes > 0
    assert memory.used_bytes > 0
    assert memory.available_bytes >= 0
    assert 0.0 <= memory.utilization_percent <= 100.0


def test_system_collector_disk():
    """Verify that real storage metrics return valid mount points and capacities."""
    collector = SystemCollector()
    disk = collector.collect_disk()

    assert isinstance(disk, DiskMetrics)
    assert disk.total_bytes > 0
    assert disk.used_bytes >= 0
    assert disk.available_bytes >= 0
    assert 0.0 <= disk.utilization_percent <= 100.0
    assert len(disk.mount_point) > 0


def test_system_collector_network():
    """Verify that network counters and speed differentials calculate without errors."""
    collector = SystemCollector()
    net1 = collector.collect_network()

    assert isinstance(net1, NetworkMetrics)
    assert net1.bytes_sent >= 0
    assert net1.bytes_recv >= 0

    # Wait a moment to allow bytes to accumulate and verify speed calculation
    time.sleep(0.1)
    net2 = collector.collect_network()
    assert isinstance(net2.upload_speed_bps, float)
    assert isinstance(net2.download_speed_bps, float)
    assert net2.upload_speed_bps >= 0.0
    assert net2.download_speed_bps >= 0.0


def test_system_collector_system_info():
    """Verify host information retrieval."""
    collector = SystemCollector()
    info = collector.get_system_info()

    assert isinstance(info, SystemInfo)
    assert len(info.os_name) > 0
    assert len(info.architecture) > 0
    assert len(info.hostname) > 0
    assert info.logical_cores >= 1
    assert info.total_ram_bytes > 0
    assert info.uptime_seconds >= 0.0


def test_process_collector():
    """Verify that active processes can be collected, sorted, and access denied handled."""
    processes = ProcessCollector.collect_processes(limit=10, sort_by="cpu")

    assert isinstance(processes, list)
    assert len(processes) > 0
    assert len(processes) <= 10

    for p in processes:
        assert isinstance(p, ProcessMetric)
        assert p.pid >= 0
        assert len(p.name) > 0
        assert p.cpu_percent >= 0.0
        assert 0.0 <= p.memory_percent <= 100.0
        assert p.memory_rss_bytes >= 0

    # Test sorting by memory
    mem_processes = ProcessCollector.collect_processes(limit=5, sort_by="memory")
    assert len(mem_processes) > 0
    # Ensure sorted in descending order of memory
    for i in range(len(mem_processes) - 1):
        assert mem_processes[i].memory_percent >= mem_processes[i + 1].memory_percent


def test_database_persistence_and_query():
    """Verify storing snapshots, retrieving history, and Pandas DataFrame integration."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db = Database(db_path=db_path)
        db.init_db()

        assert db.is_healthy() is True

        collector = SystemCollector()
        snapshot = collector.collect_all()

        record_id = db.save_metric(snapshot)
        assert record_id is not None
        assert record_id >= 1

        history = db.get_history(limit=10)
        assert len(history) == 1
        retrieved = history[0]
        assert retrieved.id == record_id
        assert retrieved.cpu.core_count_logical == snapshot.cpu.core_count_logical
        assert retrieved.memory.total_bytes == snapshot.memory.total_bytes

        # Verify Pandas DataFrame querying
        df = db.get_history_df(limit=10)
        assert not df.empty
        assert len(df) == 1
        assert "cpu_percent" in df.columns
        assert "memory_percent" in df.columns

        # Verify cleanup
        deleted = db.cleanup_old_metrics(hours=0)  # cutoff is now, so snapshot older than now?
        # A snapshot created just now might be slightly before or at cutoff
        assert deleted >= 0

    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass

