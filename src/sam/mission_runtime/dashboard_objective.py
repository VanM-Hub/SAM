# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 136 - Mission Objectives: dashboard_objective.

Read-only dashboard bridge for objectives (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .objective_summary import ObjectiveSummary


class DashboardObjectiveBridge:
    """Read-only bridge presenting objectives as cards."""

    def cards_for(self, summary: ObjectiveSummary) -> Tuple[ExecutionCard, ...]:
        ids = ", ".join(sorted(summary.objective_ids)) or "-"
        return (
            ExecutionCard(
                card_id="obj-total",
                title="Objectives",
                summary="{0} objective(s)".format(summary.total),
                detail=ids,
                verdict="ready",
            ),
            ExecutionCard(
                card_id="obj-mission",
                title="Mission",
                summary=summary.mission_id,
                detail="Objectives defined",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="obj-priority",
                title="Priority Ordered",
                summary="Objectives ranked",
                detail="By priority, deterministic",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="obj-validated",
                title="Objectives Validated",
                summary="No dangling deps",
                detail="Well-formed objectives",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="obj-sprint",
                title="Objectives Sprint 136",
                summary="Objective, builder, registry, validator, summary",
                detail="Mission Objectives",
                verdict="ready",
            ),
        )

    def verdict_card(self, summary: ObjectiveSummary) -> ExecutionCard:
        return ExecutionCard(
            card_id="obj-status",
            title="Objectives Ready",
            summary="{0} defined".format(summary.total),
            detail="Definition only - no execution",
            verdict="ready",
        )
