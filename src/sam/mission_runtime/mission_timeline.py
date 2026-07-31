# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 138 - Mission Timeline: mission_timeline.

Timeline of a mission. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .timeline_checkpoint import TimelineCheckpoint


@dataclass(frozen=True)
class MissionTimeline:
    """Immutable ordered timeline of checkpoints."""

    mission_id: str
    checkpoints: Tuple[TimelineCheckpoint, ...] = field(default_factory=tuple)

    @property
    def checkpoint_count(self) -> int:
        return len(self.checkpoints)
