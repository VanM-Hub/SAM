"""Dashboard Planner Bridge — 5 ExecutionCards (Sprint 159).

Agent Runtime — dashboard bridge read-only.
"""
from __future__ import annotations

from .mission_plan import MissionPlan
from ..dashboard.agent_dashboard import ExecutionCard


class DashboardPlannerBridge:
    """Bridge dashboard — 5 kartu untuk mission planner."""

    def __init__(self, plan: MissionPlan = None) -> None:
        self._plan = plan

    def cards(self):
        n = self._plan.step_count if self._plan else 0
        return [
            ExecutionCard("planner.plan", "planner", "ready",
                          f"{n} step(s) planned", "mission planner", "ready"),
            ExecutionCard("planner.route", "planner", "ready",
                          "pipeline route built", "deterministic", "ready"),
            ExecutionCard("planner.no_strategy", "planner", "ready",
                          "no strategy selection", "build-only", "ready"),
            ExecutionCard("planner.ordered", "planner", "ready",
                          "ordered runtime sequence", "mission plan", "ready"),
            ExecutionCard("planner.preview", "planner", "ready",
                          "preview-only planning", "no execution", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
