"""Dashboard Monitor Bridge — 5 ExecutionCards (Sprint 161).

Agent Runtime — dashboard bridge read-only.
"""
from __future__ import annotations

from .transition_monitor import TransitionMonitor
from ..dashboard.agent_dashboard import ExecutionCard


class DashboardMonitorBridge:
    """Bridge dashboard — 5 kartu untuk transition monitor."""

    def __init__(self, monitor: TransitionMonitor) -> None:
        self._monitor = monitor

    def cards(self, mission_id: str = "preview"):
        st = self._monitor.status(mission_id)
        return [
            ExecutionCard("monitor.state", "monitor", st.state,
                          f"state: {st.state}", "transition monitor", "ready"),
            ExecutionCard("monitor.progress", "monitor", "tracking",
                          f"{st.progress_percent}% complete", "progress", "ready"),
            ExecutionCard("monitor.runtime", "monitor", "ready",
                          f"runtime: {st.current_runtime or 'none'}",
                          "current runtime", "ready"),
            ExecutionCard("monitor.steps", "monitor", "ready",
                          f"{st.completed_steps} done / {st.remaining_steps} left",
                          "step tracking", "ready"),
            ExecutionCard("monitor.health", "monitor", "ready",
                          "preview-only monitoring", "read-only", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
