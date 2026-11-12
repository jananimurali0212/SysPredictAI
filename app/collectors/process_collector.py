"""Process collector for active OS processes."""
import logging
from typing import List, Optional
import psutil

from app.schemas.metrics import ProcessMetric

logger = logging.getLogger(__name__)


class ProcessCollector:
    """Collector for monitoring running system processes with robust error handling."""

    @staticmethod
    def collect_processes(limit: int = 50, sort_by: str = "cpu") -> List[ProcessMetric]:
        """Collect and return active system processes safely without crashing on access errors.

        Args:
            limit: Maximum number of processes to return.
            sort_by: Attribute to sort by ('cpu' or 'memory').

        Returns:
            List of ProcessMetric items sorted in descending order.
        """
        process_list: List[ProcessMetric] = []

        # Iterate over processes using psutil.process_iter with required attributes
        attrs = ["pid", "name", "cpu_percent", "memory_percent", "memory_info", "status", "create_time", "username"]
        for proc in psutil.process_iter(attrs=attrs):
            try:
                info = proc.info

                # Ensure process name is present
                name = info.get("name") or "unknown"
                pid = info.get("pid")
                if pid is None:
                    continue

                cpu_percent = info.get("cpu_percent") or 0.0
                memory_percent = info.get("memory_percent") or 0.0
                mem_info = info.get("memory_info")
                rss = mem_info.rss if mem_info and hasattr(mem_info, "rss") else 0
                status = info.get("status") or "unknown"
                create_time = info.get("create_time")
                username = info.get("username")

                metric = ProcessMetric(
                    pid=int(pid),
                    name=str(name),
                    cpu_percent=round(float(cpu_percent), 2),
                    memory_percent=round(float(memory_percent), 2),
                    memory_rss_bytes=int(rss),
                    status=str(status),
                    create_time=float(create_time) if create_time else None,
                    username=str(username) if username else None,
                )
                process_list.append(metric)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Processes frequently terminate or reject access for non-elevated callers
                continue
            except Exception as e:
                # Shield collector from unexpected process inspection failures
                logger.debug("Failed to read process details: %s", e)
                continue

        # Sort the processes
        if sort_by == "memory":
            process_list.sort(key=lambda p: (p.memory_percent, p.memory_rss_bytes), reverse=True)
        else:
            # default to cpu
            process_list.sort(key=lambda p: (p.cpu_percent, p.memory_percent), reverse=True)

        return process_list[: max(1, limit)]

