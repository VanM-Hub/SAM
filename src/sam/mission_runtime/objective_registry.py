# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 136 - Mission Objectives: objective_registry.

Registry of objectives. Pure in-memory, sync.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, FrozenSet

from .mission_objective import MissionObjective


@dataclass(frozen=True)
class ObjectiveRegistrationResult:
    objective_id: str
    accepted: bool
    reason: str = ""


class ObjectiveRegistry:
    """Catalog of mission objectives."""

    def __init__(self) -> None:
        self._objectives: Dict[str, MissionObjective] = {}

    def register(self, objective: MissionObjective) -> ObjectiveRegistrationResult:
        self._objectives[objective.objective_id] = objective
        return ObjectiveRegistrationResult(
            objective_id=objective.objective_id, accepted=True, reason="registered"
        )

    def get(self, objective_id: str) -> Optional[MissionObjective]:
        return self._objectives.get(objective_id)

    def all(self) -> Tuple[MissionObjective, ...]:
        return tuple(
            sorted(self._objectives.values(), key=lambda o: (o.priority, o.objective_id))
        )

    def ids(self) -> FrozenSet[str]:
        return frozenset(self._objectives.keys())

    def count(self) -> int:
        return len(self._objectives)
