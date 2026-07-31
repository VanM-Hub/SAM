# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 136 - Mission Objectives: objective_builder.

Builds objectives for a mission (planning only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .mission_objective import MissionObjective
from .objective_registry import ObjectiveRegistry


@dataclass(frozen=True)
class ObjectiveBuildResult:
    objective: MissionObjective
    accepted: bool = True


class ObjectiveBuilder:
    """Creates and registers objectives."""

    def __init__(self, registry: ObjectiveRegistry) -> None:
        self._registry = registry

    def add(
        self, objective_id: str, title: str, priority: int = 0
    ) -> ObjectiveBuildResult:
        objective = MissionObjective(
            objective_id=objective_id, title=title, priority=priority
        )
        self._registry.register(objective)
        return ObjectiveBuildResult(objective=objective, accepted=True)
