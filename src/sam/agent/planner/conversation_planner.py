"""Conversation Planner Bridge — query read-only (Sprint 159)."""
from __future__ import annotations
from typing import List

from .mission_plan import MissionPlan
from .mission_route import PIPELINE_ROUTE


class ConversationPlannerBridge:
    """Bridge conversation — ringkasan rencana mission read-only."""

    def __init__(self, plan: MissionPlan = None) -> None:
        self._plan = plan

    def show_pipeline(self) -> List[str]:
        if self._plan is None:
            return list(PIPELINE_ROUTE)
        return [s.runtime_name for s in self._plan.ordered_steps()]

    def show_step_count(self) -> int:
        return self._plan.step_count if self._plan else 0

    def show_remaining_steps(self, done: int = 0) -> int:
        total = self.show_step_count()
        return max(0, total - done)
