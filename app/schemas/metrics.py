"""Pydantic models for hardware metrics, system information, and API responses."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CPUFrequency(BaseModel):
    """CPU Frequency information in MHz."""
    current: Optional[float] = Field(None, description="Current frequency in MHz")
    min: Optional[float] = Field(None, description="Minimum frequency in MHz")
    max: Optional[float] = Field(None, description="Maximum frequency in MHz")


class CPUMetrics(BaseModel):
    """CPU Performance metrics."""
    utilization_percent: float = Field(..., ge=0.0, description="Overall CPU usage percentage")
    per_core_utilization: List[float] = Field(..., description="Per-core CPU usage percentages")
    core_count_physical: Optional[int] = Field(None, description="Number of physical CPU cores")
    core_count_logical: int = Field(..., description="Number of logical CPU cores")
    frequency: Optional[CPUFrequency] = Field(None, description="CPU frequency if available")


class MemoryMetrics(BaseModel):
    """RAM memory metrics."""
    total_bytes: int = Field(..., ge=0, description="Total physical memory in bytes")
    used_bytes: int = Field(..., ge=0, description="Used physical memory in bytes")
    available_bytes: int = Field(..., ge=0, description="Available physical memory in bytes")
    utilization_percent: float = Field(..., ge=0.0, le=100.0, description="Memory utilization percentage")


class DiskMetrics(BaseModel):
    """Storage drive metrics."""
    mount_point: str = Field(..., description="Mount point or drive letter")
    total_bytes: int = Field(..., ge=0, description="Total storage capacity in bytes")
    used_bytes: int = Field(..., ge=0, description="Used storage capacity in bytes")
    available_bytes: int = Field(..., ge=0, description="Available free storage in bytes")
    utilization_percent: float = Field(..., ge=0.0, le=100.0, description="Disk utilization percentage")


class NetworkMetrics(BaseModel):
    """Network I/O and bandwidth metrics."""
    bytes_sent: int = Field(..., ge=0, description="Total bytes sent since boot")
    bytes_recv: int = Field(..., ge=0, description="Total bytes received since boot")
    upload_speed_bps: float = Field(..., ge=0.0, description="Current upload speed in bytes per second")
    download_speed_bps: float = Field(..., ge=0.0, description="Current download speed in bytes per second")


class SystemMetricsSnapshot(BaseModel):
    """Complete snapshot of system telemetry at a point in time."""
    id: Optional[int] = Field(None, description="Database record ID if persisted")
    timestamp: datetime = Field(..., description="UTC timestamp of the measurement")
    cpu: CPUMetrics
    memory: MemoryMetrics
    disk: DiskMetrics
    network: NetworkMetrics


class ProcessMetric(BaseModel):
    """Detailed information for an individual OS process."""
    pid: int = Field(..., description="Process identifier")
    name: str = Field(..., description="Process name or executable")
    cpu_percent: float = Field(..., ge=0.0, description="Process CPU utilization percentage")
    memory_percent: float = Field(..., ge=0.0, le=100.0, description="Process memory percentage")
    memory_rss_bytes: int = Field(..., ge=0, description="Resident Set Size in bytes")
    status: str = Field(..., description="Process execution status (running, sleeping, etc.)")
    create_time: Optional[float] = Field(None, description="Process creation timestamp")
    username: Optional[str] = Field(None, description="User running the process")


class ProcessListResponse(BaseModel):
    """Response payload for process list queries."""
    count: int = Field(..., description="Total count of returned processes")
    processes: List[ProcessMetric] = Field(..., description="List of process metrics")


class SystemInfo(BaseModel):
    """Static and semi-static host machine metadata."""
    os_name: str = Field(..., description="Operating system name")
    os_version: str = Field(..., description="Operating system release version")
    architecture: str = Field(..., description="Machine architecture (e.g., AMD64, x86_64)")
    hostname: str = Field(..., description="Host network name")
    boot_time: datetime = Field(..., description="System boot timestamp")
    uptime_seconds: float = Field(..., ge=0.0, description="System uptime in seconds")
    python_version: str = Field(..., description="Python runtime version")
    cpu_model: Optional[str] = Field(None, description="CPU model name / processor string")
    physical_cores: Optional[int] = Field(None, description="Physical CPU cores")
    logical_cores: int = Field(..., description="Logical CPU cores")
    total_ram_bytes: int = Field(..., description="Total physical memory in bytes")


class HealthResponse(BaseModel):
    """Health check payload."""
    status: str = Field(..., description="Overall service status ('healthy' or 'degraded')")
    timestamp: datetime = Field(..., description="Current UTC timestamp")
    version: str = Field(..., description="Service version")
    uptime_seconds: float = Field(..., ge=0.0, description="API server uptime in seconds")
    collectors_healthy: bool = Field(..., description="True if telemetry collectors are functioning")
    database_healthy: bool = Field(..., description="True if SQLite database is responsive")


class HistoricalMetricsResponse(BaseModel):
    """Response payload for historical metrics."""
    count: int = Field(..., description="Number of metric snapshots returned")
    metrics: List[SystemMetricsSnapshot] = Field(..., description="List of historical snapshots")

