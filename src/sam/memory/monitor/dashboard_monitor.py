"""Dashboard Monitor Bridge — 5 ExecutionCards (Sprint 177)."""
from __future__ import annotations

from .memory_monitor import MemoryMonitor
from ..dashboard.memory_dashboard import ExecutionCard


class DashboardMonitorBridge:
    """Bridge dashboard — 5 kartu untuk memory monitor."""

    def __init__(self, monitor: MemoryMonitor) -> None:
        self._monitor = monitor

    def cards(self):
        n = len(self._monitor.all_status())
        healthy = self._monitor.healthy_count()
        return [
            ExecutionCard("monitor.memories", "monitor", "ready",
                          f"{n} memory(s) tracked", "memory monitor", "ready"),
            ExecutionCard("monitor.health", "monitor", "ready",
                          f"{healthy} healthy", "health check", "ready"),
            ExecutionCard("monitor.metrics", "monitor", "ready",
                          "metrics collected", "read-only", "ready"),
            ExecutionCard("monitor.snapshot", "monitor", "ready",
                          "snapshot available", "monitor", "ready"),
            ExecutionCard("monitor.external", "monitor", "ready",
                          "external_calls=0", "preview", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
