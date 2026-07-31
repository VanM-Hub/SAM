"""Dashboard Execution Foundation (Sprint 250).

Program C - Real Execution Runtime.
Read-only bridge: ringkasan foundation execution untuk dashboard.
"""
from __future__ import annotations
from typing import Dict, List

from .execution_registry import ExecutionRegistry
from .execution_descriptor import ExecutionDescriptor


class DashboardExecutionFoundation:
    """Bridge execution foundation <-> dashboard. Read-only, no network."""

    def __init__(self, registry: ExecutionRegistry | None = None) -> None:
        self._registry = registry or ExecutionRegistry()
        self._buckets: Dict[str, int] = {"preview": 0, "execute": 0, "rollback": 0}

    def add(self, descriptor: ExecutionDescriptor) -> None:
        self._registry.register(descriptor)
        if descriptor.mode in self._buckets:
            self._buckets[descriptor.mode] += 1

    def rows(self) -> List[dict]:
        return [
            {"mode": m, "count": self._buckets[m], "external_calls": 0}
            for m in ("preview", "execute", "rollback")
        ]

    def summary(self) -> Dict[str, object]:
        return {
            "total": sum(self._buckets.values()),
            "by_mode": dict(self._buckets),
            "external_calls": 0,
        }
