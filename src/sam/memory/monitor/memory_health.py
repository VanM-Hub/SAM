"""Memory Health — kesehatan memori (Sprint 177).

Phase XVII — Memory Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.memory_registry import MemoryRegistry
from .memory_monitor import MemoryMonitor


@dataclass(frozen=True)
class MemoryHealth:
    """Kesehatan memori (immutable)."""
    healthy: bool = True
    total: int = 0
    healthy_memories: int = 0
    issues: List[str] = field(default_factory=list)


class MemoryHealthCheck:
    """Health check memori. Read-only."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry
        self._monitor = MemoryMonitor(registry)

    def check(self) -> MemoryHealth:
        statuses = self._monitor.all_status()
        healthy = sum(1 for s in statuses if s.healthy)
        issues = [f"{s.memory_id} unregistered" for s in statuses if not s.registered]
        return MemoryHealth(
            healthy=len(issues) == 0,
            total=len(statuses),
            healthy_memories=healthy,
            issues=issues,
        )
