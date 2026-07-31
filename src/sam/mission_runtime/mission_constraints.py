# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 135 - Mission Definition: mission_constraints.

Constraints applied to a mission. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class MissionConstraints:
    """Immutable operating constraints for a mission."""

    max_objectives: int = 0
    preview_only: bool = True
    allowed_actions: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_plan_only(self) -> bool:
        return self.preview_only
