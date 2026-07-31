# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 138 - Mission Timeline: timeline_builder.

Builds a mission timeline from labels (planning only).
"""
from __future__ import annotations

from typing import Tuple

from .timeline_checkpoint import TimelineCheckpoint
from .mission_timeline import MissionTimeline


class TimelineBuilder:
    """Builds an ordered timeline of checkpoints."""

    def build(
        self, mission_id: str, labels: Tuple[str, ...]
    ) -> MissionTimeline:
        checkpoints = tuple(
            TimelineCheckpoint(
                checkpoint_id="{0}-cp{1}".format(mission_id, idx),
                order=idx,
                label=label,
            )
            for idx, label in enumerate(labels)
        )
        return MissionTimeline(mission_id=mission_id, checkpoints=checkpoints)
