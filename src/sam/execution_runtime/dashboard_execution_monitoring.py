"""Dashboard Execution Monitoring (Sprint 256).

Program C - Real Execution Runtime.
Read-only bridge: ringkasan monitoring untuk dashboard.
"""
from __future__ import annotations
from typing import Dict, List

from .execution_monitor import ExecutionMonitor


class DashboardExecutionMonitoring:
    """Bridge monitoring <-> dashboard. Read-only, no network."""

    def __init__(self, monitor: ExecutionMonitor | None = None) -> None:
        self._monitor = monitor or ExecutionMonitor()

    def summary(self) -> Dict[str, object]:
        h = self._monitor.health()
        return {
            "recorded": self._monitor.history.count(),
            "healthy": h.ok,
            "health_status": h.status,
            "external_calls": 0,
        }
