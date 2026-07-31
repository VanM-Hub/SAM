"""Dashboard Monitor Bridge — 5 ExecutionCards (Sprint 185)."""
from __future__ import annotations

from .knowledge_monitor import KnowledgeMonitor
from ..dashboard.knowledge_dashboard import ExecutionCard


class DashboardMonitorBridge:
    """Bridge dashboard — 5 kartu untuk knowledge monitor."""

    def __init__(self, monitor: KnowledgeMonitor) -> None:
        self._monitor = monitor

    def cards(self):
        n = len(self._monitor.all_status())
        healthy = self._monitor.healthy_count()
        return [
            ExecutionCard("monitor.knowledge", "monitor", "ready",
                          f"{n} knowledge(s) tracked", "knowledge monitor", "ready"),
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
