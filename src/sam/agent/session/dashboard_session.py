"""Dashboard Session Bridge — 5 ExecutionCards (Sprint 157).

Agent Runtime — dashboard bridge read-only.
"""
from __future__ import annotations

from .mission_registry import MissionRegistry
from ..dashboard.agent_dashboard import ExecutionCard


class DashboardSessionBridge:
    """Bridge dashboard — 5 kartu untuk mission session."""

    def __init__(self, registry: MissionRegistry) -> None:
        self._registry = registry

    def cards(self):
        sm = self._registry.session_summary()
        missions = self._registry.count_missions()
        return [
            ExecutionCard("session.overview", "session", "ready",
                          f"{sm.total} session(s), {missions} mission(s)",
                          "mission session", "ready"),
            ExecutionCard("session.open", "session", "ready",
                          f"{sm.open} open", "session summary", "ready"),
            ExecutionCard("session.active", "session", "ready",
                          f"{sm.active} active", "session summary", "ready"),
            ExecutionCard("session.external", "session", "ready",
                          "external_calls=0", "preview-only", "ready"),
            ExecutionCard("session.state", "session", "ready",
                          "state tracked", "mission state", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
