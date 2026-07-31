"""Mission Plan — rencana mission (Sprint 159).

Agent Runtime — planner hanya membangun urutan runtime. Tidak memilih strategi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .mission_step import MissionStep  # noqa: F401  (re-export kemudahan)


@dataclass(frozen=True)
class MissionPlan:
    """Rencana mission (immutable)."""
    plan_id: str
    mission_id: str
    steps: List["MissionStep"] = field(default_factory=list)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def ordered_steps(self) -> List["MissionStep"]:
        return sorted(self.steps, key=lambda s: s.order)
