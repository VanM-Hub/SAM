# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 140 - Mission Coordination: coordination_registry.

Registry of coordination plans. Pure in-memory, sync.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .coordination_plan import CoordinationPlan


@dataclass(frozen=True)
class CoordinationRegistrationResult:
    mission_id: str
    accepted: bool
    reason: str = ""


class CoordinationRegistry:
    """Holds coordination plans per mission."""

    def __init__(self) -> None:
        self._plans: Dict[str, CoordinationPlan] = {}

    def register(self, plan: CoordinationPlan) -> CoordinationRegistrationResult:
        self._plans[plan.mission_id] = plan
        return CoordinationRegistrationResult(
            mission_id=plan.mission_id, accepted=True, reason="registered"
        )

    def get(self, mission_id: str) -> Optional[CoordinationPlan]:
        return self._plans.get(mission_id)

    def all(self) -> Tuple[CoordinationPlan, ...]:
        return tuple(sorted(self._plans.values(), key=lambda p: p.mission_id))

    def count(self) -> int:
        return len(self._plans)
