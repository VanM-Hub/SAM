# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 140 - Mission Coordination: dashboard_coordination.

Read-only dashboard bridge for coordination (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .coordination_plan import CoordinationPlan


class DashboardCoordinationBridge:
    """Read-only bridge presenting coordination as cards."""

    def cards_for(self, plan: CoordinationPlan) -> Tuple[ExecutionCard, ...]:
        runtimes = ", ".join(plan.runtimes) or "-"
        return (
            ExecutionCard(
                card_id="cord-mission",
                title="Mission",
                summary=plan.mission_id,
                detail="Coordinated across runtimes",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="cord-runtimes",
                title="Runtimes Coordinated",
                summary="{0} runtime(s)".format(plan.runtime_count),
                detail=runtimes,
                verdict="ready",
            ),
            ExecutionCard(
                card_id="cord-plan",
                title="Coordination Plan",
                summary="plan-only",
                detail="Arranges, does not run",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="cord-validated",
                title="Plan Validated",
                summary="No duplicates",
                detail="Well-formed coordination",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="cord-sprint",
                title="Coordination Sprint 140",
                summary="Coordinator, plan, registry, validator, summary",
                detail="Mission Coordination",
                verdict="ready",
            ),
        )

    def verdict_card(self, plan: CoordinationPlan) -> ExecutionCard:
        return ExecutionCard(
            card_id="cord-status",
            title="Mission Coordinated",
            summary="coordinated {0} runtime(s)".format(plan.runtime_count),
            detail="Coordination only - no execution",
            verdict="ready",
        )
