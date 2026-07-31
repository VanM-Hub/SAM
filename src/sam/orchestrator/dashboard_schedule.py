# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 128 - Scheduling: dashboard_schedule.

Read-only dashboard bridge for scheduling (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .schedule_plan import SchedulePlan


class DashboardScheduleBridge:
    """Read-only bridge presenting schedule as cards."""

    def cards_for(self, plan: SchedulePlan) -> Tuple[ExecutionCard, ...]:
        order = ", ".join(plan.order) or "-"
        return (
            ExecutionCard(
                card_id="sched-order",
                title="Execution Order",
                summary="{0} stage(s)".format(plan.stage_count),
                detail=order,
                verdict="ready",
            ),
            ExecutionCard(
                card_id="sched-plan",
                title="Schedule Plan",
                summary="Ordered execution plan",
                detail="Plan only - not run",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="sched-validated",
                title="Schedule Validated",
                summary="No duplicates/empty",
                detail="Deterministic order",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="sched-registry",
                title="Schedule Registry",
                summary="Plans stored",
                detail="Keyed by schedule_id",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="sched-sprint",
                title="Scheduling Sprint 128",
                summary="Request, plan, validator, registry, summary",
                detail="Scheduling",
                verdict="ready",
            ),
        )

    def verdict_card(self, plan: SchedulePlan) -> ExecutionCard:
        return ExecutionCard(
            card_id="sched-status",
            title="Scheduled",
            summary="execution order ready".format(plan.stage_count),
            detail="Schedules only - no execution",
            verdict="ready",
        )
