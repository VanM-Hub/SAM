# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 140 - Mission Coordination: conversation_coordination.

Read-only conversation bridge for coordination.
"""
from __future__ import annotations

from typing import Optional, Tuple

from .mission_coordinator import MissionCoordinator
from .coordination_plan import CoordinationPlan
from .coordination_registry import CoordinationRegistry
from .coordination_summary import CoordinationSummary


class ConversationCoordinationBridge:
    """Read-only bridge exposing coordination."""

    def __init__(self, coordinator: MissionCoordinator) -> None:
        self._coordinator = coordinator
        self._registry = coordinator._registry

    def coordinate(self, mission_id: str, runtimes: Tuple[str, ...]) -> CoordinationPlan:
        return self._coordinator.coordinate(mission_id, runtimes)

    def plan_of(self, mission_id: str) -> Optional[CoordinationPlan]:
        return self._registry.get(mission_id)

    def summarize(self, plan: CoordinationPlan) -> CoordinationSummary:
        return CoordinationSummary(
            mission_id=plan.mission_id,
            runtimes=plan.runtimes,
            total=plan.runtime_count,
        )
