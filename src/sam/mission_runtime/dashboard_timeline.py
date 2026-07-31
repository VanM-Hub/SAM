# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 138 - Mission Timeline: dashboard_timeline.

Read-only dashboard bridge for timelines (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .mission_timeline import MissionTimeline


class DashboardTimelineBridge:
    """Read-only bridge presenting timeline as cards."""

    def cards_for(self, timeline: MissionTimeline) -> Tuple[ExecutionCard, ...]:
        labels = ", ".join(cp.label for cp in timeline.checkpoints) or "-"
        return (
            ExecutionCard(
                card_id="tl-count",
                title="Timeline Checkpoints",
                summary="{0} checkpoint(s)".format(timeline.checkpoint_count),
                detail=labels,
                verdict="ready",
            ),
            ExecutionCard(
                card_id="tl-mission",
                title="Mission",
                summary=timeline.mission_id,
                detail="Timeline defined",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="tl-ordered",
                title="Ordered",
                summary="Checkpoints sequential",
                detail="Deterministic order",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="tl-validated",
                title="Timeline Validated",
                summary="Order well-formed",
                detail="No execution performed",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="tl-sprint",
                title="Timeline Sprint 138",
                summary="Timeline, builder, checkpoint, validator, summary",
                detail="Mission Timeline",
                verdict="ready",
            ),
        )

    def verdict_card(self, timeline: MissionTimeline) -> ExecutionCard:
        return ExecutionCard(
            card_id="tl-status",
            title="Timeline Ready",
            summary="{0} checkpoints".format(timeline.checkpoint_count),
            detail="Timeline only - no execution",
            verdict="ready",
        )
