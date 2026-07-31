# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 136 - Mission Objectives: mission_objective.

A single objective of a mission. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class MissionObjective:
    """Immutable objective within a mission."""

    objective_id: str
    title: str = ""
    priority: int = 0
    depends_on: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_identifiable(self) -> bool:
        return bool(self.objective_id)
