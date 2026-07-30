"""Resource Monitor — monitoring resource."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_health import ResourceUsage


class ResourceMonitor:
    """Monitor resource — preview-only."""

    def __init__(self) -> None:
        self._usages: Dict[str, ResourceUsage] = {}

    def record(self, usage_id: str, cpu_pct: float, memory_pct: float,
               subsystem: str = "kernel") -> ResourceUsage:
        u = ResourceUsage(
            usage_id=usage_id,
            cpu_pct=cpu_pct,
            memory_pct=memory_pct,
            subsystem=subsystem,
        )
        self._usages[usage_id] = u
        return u

    def get(self, usage_id: str) -> ResourceUsage | None:
        return self._usages.get(usage_id)

    def cpu_avg(self) -> float:
        if not self._usages:
            return 0.0
        return sum(u.cpu_pct for u in self._usages.values()) / len(self._usages)

    def memory_avg(self) -> float:
        if not self._usages:
            return 0.0
        return sum(u.memory_pct for u in self._usages.values()) / len(self._usages)

    def count(self) -> int:
        return len(self._usages)
