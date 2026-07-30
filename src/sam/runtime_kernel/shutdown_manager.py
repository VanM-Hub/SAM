"""Shutdown Manager — shutdown runtime."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.runtime_lifecycle import ShutdownPlan


class ShutdownManager:
    """Manager shutdown — preview-only."""

    SHUTDOWN_TASKS = ["suspend_subsystems", "save_state", "close_connections", "finalize"]

    def create_plan(self, plan_id: str, reason: str = "", graceful: bool = True) -> ShutdownPlan:
        return ShutdownPlan(
            plan_id=plan_id,
            reason=reason,
            graceful=graceful,
            total_tasks=len(self.SHUTDOWN_TASKS),
        )

    def list_tasks(self) -> List[str]:
        return list(self.SHUTDOWN_TASKS)

    def count_tasks(self) -> int:
        return len(self.SHUTDOWN_TASKS)
