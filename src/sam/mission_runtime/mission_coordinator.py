# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 140 - Mission Coordination: mission_coordinator.

Coordinates all runtimes toward a single mission (planning only).
Arranges and directs; never executes.
"""
from __future__ import annotations

from typing import Tuple

from .coordination_plan import CoordinationPlan
from .coordination_registry import CoordinationRegistry


class MissionCoordinator:
    """Coordinates a mission across runtimes (plan-only)."""

    def __init__(self, registry: CoordinationRegistry) -> None:
        self._registry = registry

    def coordinate(self, mission_id: str, runtimes: Tuple[str, ...]) -> CoordinationPlan:
        plan = CoordinationPlan(mission_id=mission_id, runtimes=runtimes)
        self._registry.register(plan)
        return plan

    def registered(self) -> int:
        return self._registry.count()
