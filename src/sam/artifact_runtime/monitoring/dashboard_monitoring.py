"""Dashboard Monitoring Bridge — 5 PolicyCards (Sprint 225)."""
from __future__ import annotations

from ..dashboard import PolicyCard


class DashboardMonitoringBridge:
    """Bridge dashboard — 5 kartu monitoring artifact."""

    def cards(self):
        return [
            PolicyCard("am.monitor", "artifact", "ready",
                       "status preview-only", "monitoring", "ready"),
            PolicyCard("am.metrics", "artifact", "ready",
                       "metrics external_calls=0", "monitoring", "ready"),
            PolicyCard("am.health", "artifact", "ready",
                       "healthy deterministic", "monitoring", "ready"),
            PolicyCard("am.snapshot", "artifact", "ready",
                       "read-only snapshot", "monitoring", "ready"),
            PolicyCard("am.report", "artifact", "ready",
                       "report ready", "monitoring", "ready"),
        ]
