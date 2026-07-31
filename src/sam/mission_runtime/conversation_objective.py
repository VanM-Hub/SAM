# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 136 - Mission Objectives: conversation_objective.

Read-only conversation bridge for objectives.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

from .objective_registry import ObjectiveRegistry
from .objective_builder import ObjectiveBuilder, ObjectiveBuildResult
from .objective_summary import ObjectiveSummary
from .mission_objective import MissionObjective


class ConversationObjectiveBridge:
    """Read-only bridge exposing objectives."""

    def __init__(self, registry: ObjectiveRegistry) -> None:
        self._registry = registry
        self._builder = ObjectiveBuilder(registry)

    def add(self, objective_id: str, title: str, priority: int = 0) -> ObjectiveBuildResult:
        return self._builder.add(objective_id, title, priority)

    def locate(self, objective_id: str) -> Optional[MissionObjective]:
        return self._registry.get(objective_id)

    def count(self) -> int:
        return self._registry.count()

    def summarize(self, mission_id: str) -> ObjectiveSummary:
        return ObjectiveSummary(
            mission_id=mission_id,
            objective_ids=self._registry.ids(),
            total=self._registry.count(),
        )
