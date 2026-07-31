# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 128 - Scheduling: schedule_plan.

A produced execution-order plan. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class SchedulePlan:
    """Immutable schedule: an ordered execution plan of runtimes."""

    schedule_id: str
    order: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def stage_count(self) -> int:
        return len(self.order)
