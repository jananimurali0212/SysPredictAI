"""System collector for host hardware performance metrics."""
import logging
import os
import platform
import threading
import time
from datetime import datetime, timezone
from typing import Optional

import psutil

from app.schemas.metrics import (
    CPUFrequency,
    CPUMetrics,
    DiskMetrics,
    MemoryMetrics,
    NetworkMetrics,
    SystemInfo,
    SystemMetricsSnapshot,
)

logger = logging.getLogger(__name__)


class SystemCollector:
    """Thread-safe collector for real system hardware performance metrics."""

    def __init__(self, disk_mount: Optional[str] = None):
        self._lock = threading.Lock()
        self._disk_mount = disk_mount or self._detect_default_mount()

        # Prime the CPU percent calculation so subsequent non-blocking calls return meaningful values
        try:
            psutil.cpu_percent(interval=None)
            psutil.cpu_percent(interval=None, percpu=True)
        except Exception as e:
            logger.warning("Failed to prime CPU counters: %s", e)

        # Initialize network counters for speed differential calculation
        self._prev_net_time: float = time.time()
        try:
            net_io = psutil.net_io_counters()
            self._prev_bytes_sent: int = net_io.bytes_sent
            self._prev_bytes_recv: int = net_io.bytes_recv
        except Exception as e:
            logger.warning("Failed to initialize network counters: %s", e)
            self._prev_bytes_sent = 0
            self._prev_bytes_recv = 0

    @staticmethod
    def _detect_default_mount() -> str:
        """Determine appropriate root disk mount point for the current OS."""
        if platform.system() == "Windows":
            system_drive = os.environ.get("SystemDrive", "C:")
            return f"{system_drive}\\" if not system_drive.endswith("\\") else system_drive
        return "/"

    def collect_cpu(self) -> CPUMetrics:
        """Collect real CPU utilization, per-core utilization, core counts, and frequency."""
        try:
            utilization = psutil.cpu_percent(interval=None)
            per_core = psutil.cpu_percent(interval=None, percpu=True)
            physical_cores = psutil.cpu_count(logical=False)
            logical_cores = psutil.cpu_count(logical=True) or len(per_core) or 1

            frequency: Optional[CPUFrequency] = None
            try:
                freq = psutil.cpu_freq()
                if freq is not None:
                    frequency = CPUFrequency(
                        current=round(freq.current, 2) if freq.current else None,
                        min=round(freq.min, 2) if freq.min else None,
                        max=round(freq.max, 2) if freq.max else None,
                    )
            except Exception as fe:
                logger.debug("CPU frequency unavailable: %s", fe)

            return CPUMetrics(
                utilization_percent=round(float(utilization), 2),
                per_core_utilization=[round(float(c), 2) for c in per_core],
                core_count_physical=physical_cores,
                core_count_logical=logical_cores,
                frequency=frequency,
            )
        except Exception as e:
            logger.error("Error collecting CPU metrics: %s", e, exc_info=True)
            return CPUMetrics(
                utilization_percent=0.0,
                per_core_utilization=[],
                core_count_physical=None,
                core_count_logical=1,
                frequency=None,
            )

    def collect_memory(self) -> MemoryMetrics:
        """Collect real RAM usage metrics."""
        try:
            vm = psutil.virtual_memory()
            return MemoryMetrics(
                total_bytes=int(vm.total),
                used_bytes=int(vm.used),
                available_bytes=int(vm.available),
                utilization_percent=round(float(vm.percent), 2),
            )
        except Exception as e:
            logger.error("Error collecting Memory metrics: %s", e, exc_info=True)
            return MemoryMetrics(
                total_bytes=0,
                used_bytes=0,
                available_bytes=0,
                utilization_percent=0.0,
            )

    def collect_disk(self) -> DiskMetrics:
        """Collect real Disk storage utilization."""
        try:
            mount = self._disk_mount
            try:
                usage = psutil.disk_usage(mount)
            except Exception:
                # Fallback to current working directory root if default mount fails
                fallback = os.path.abspath(os.sep)
                usage = psutil.disk_usage(fallback)
                mount = fallback

            return DiskMetrics(
                mount_point=mount,
                total_bytes=int(usage.total),
                used_bytes=int(usage.used),
                available_bytes=int(usage.free),
                utilization_percent=round(float(usage.percent), 2),
            )
        except Exception as e:
            logger.error("Error collecting Disk metrics: %s", e, exc_info=True)
            return DiskMetrics(
                mount_point=self._disk_mount,
                total_bytes=0,
                used_bytes=0,
                available_bytes=0,
                utilization_percent=0.0,
            )

    def collect_network(self) -> NetworkMetrics:
        """Collect real network byte totals and calculate instantaneous upload/download speeds."""
        with self._lock:
            now = time.time()
            elapsed = now - self._prev_net_time

            try:
                net_io = psutil.net_io_counters()
                bytes_sent = int(net_io.bytes_sent)
                bytes_recv = int(net_io.bytes_recv)

                if elapsed > 0.05:
                    delta_sent = bytes_sent - self._prev_bytes_sent
                    delta_recv = bytes_recv - self._prev_bytes_recv

                    # Handle counter rollover or system time adjustments gracefully
                    upload_speed = max(0.0, delta_sent / elapsed) if delta_sent >= 0 else 0.0
                    download_speed = max(0.0, delta_recv / elapsed) if delta_recv >= 0 else 0.0

                    self._prev_bytes_sent = bytes_sent
                    self._prev_bytes_recv = bytes_recv
                    self._prev_net_time = now
                else:
                    upload_speed = 0.0
                    download_speed = 0.0

                return NetworkMetrics(
                    bytes_sent=bytes_sent,
                    bytes_recv=bytes_recv,
                    upload_speed_bps=round(float(upload_speed), 2),
                    download_speed_bps=round(float(download_speed), 2),
                )
            except Exception as e:
                logger.error("Error collecting Network metrics: %s", e, exc_info=True)
                return NetworkMetrics(
                    bytes_sent=0,
                    bytes_recv=0,
                    upload_speed_bps=0.0,
                    download_speed_bps=0.0,
                )

    def collect_all(self) -> SystemMetricsSnapshot:
        """Collect all system metrics in a unified timestamped snapshot."""
        timestamp = datetime.now(timezone.utc)
        cpu = self.collect_cpu()
        memory = self.collect_memory()
        disk = self.collect_disk()
        network = self.collect_network()

        return SystemMetricsSnapshot(
            timestamp=timestamp,
            cpu=cpu,
            memory=memory,
            disk=disk,
            network=network,
        )

    def get_system_info(self) -> SystemInfo:
        """Retrieve host machine platform, CPU, and memory hardware details."""
        try:
            boot_ts = psutil.boot_time()
            boot_dt = datetime.fromtimestamp(boot_ts, tz=timezone.utc)
            uptime = max(0.0, time.time() - boot_ts)
            phys_cores = psutil.cpu_count(logical=False)
            log_cores = psutil.cpu_count(logical=True) or 1
            total_ram = psutil.virtual_memory().total

            cpu_model = platform.processor() or platform.uname().processor or None

            return SystemInfo(
                os_name=platform.system(),
                os_version=platform.release(),
                architecture=platform.machine(),
                hostname=platform.node(),
                boot_time=boot_dt,
                uptime_seconds=round(uptime, 2),
                python_version=platform.python_version(),
                cpu_model=cpu_model,
                physical_cores=phys_cores,
                logical_cores=log_cores,
                total_ram_bytes=int(total_ram),
            )
        except Exception as e:
            logger.error("Error retrieving system information: %s", e, exc_info=True)
            return SystemInfo(
                os_name=platform.system(),
                os_version=platform.release(),
                architecture=platform.machine(),
                hostname="unknown",
                boot_time=datetime.now(timezone.utc),
                uptime_seconds=0.0,
                python_version=platform.python_version(),
                cpu_model=None,
                physical_cores=None,
                logical_cores=1,
                total_ram_bytes=0,
            )

