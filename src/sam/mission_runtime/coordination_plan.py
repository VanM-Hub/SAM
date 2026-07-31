# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 140 - Mission Coordination: coordination_plan.

A plan to coordinate a mission. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class CoordinationPlan:
    """Immutable coordination plan for a mission."""

    mission_id: str
    runtimes: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def runtime_count(self) -> int:
        return len(self.runtimes)

    @property
    def is_plan_only(self) -> bool:
        return True
