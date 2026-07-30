"""Restart Manager — restart runtime."""
from __future__ import annotations
from sam.runtime_kernel.runtime_lifecycle import RestartPlan


class RestartManager:
    """Manager restart — preview-only."""

    def create_plan(self, plan_id: str, shutdown_id: str, startup_id: str) -> RestartPlan:
        return RestartPlan(
            plan_id=plan_id,
            shutdown_id=shutdown_id,
            startup_id=startup_id,
            status="pending",
        )

    def complete_plan(self, plan: RestartPlan) -> RestartPlan:
        return RestartPlan(
            plan_id=plan.plan_id,
            shutdown_id=plan.shutdown_id,
            startup_id=plan.startup_id,
            status="completed",
        )
