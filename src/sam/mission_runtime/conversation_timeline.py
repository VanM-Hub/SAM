# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 138 - Mission Timeline: conversation_timeline.

Read-only conversation bridge for timelines.
"""
from __future__ import annotations

from typing import Tuple

from .timeline_builder import TimelineBuilder
from .mission_timeline import MissionTimeline
from .timeline_summary import TimelineSummary


class ConversationTimelineBridge:
    """Read-only bridge exposing timeline building."""

    def __init__(self) -> None:
        self._builder = TimelineBuilder()

    def build(self, mission_id: str, labels: Tuple[str, ...]) -> MissionTimeline:
        return self._builder.build(mission_id, labels)

    def summarize(self, timeline: MissionTimeline) -> TimelineSummary:
        return TimelineSummary(
            mission_id=timeline.mission_id,
            labels=tuple(cp.label for cp in timeline.checkpoints),
            total_checkpoints=timeline.checkpoint_count,
        )
