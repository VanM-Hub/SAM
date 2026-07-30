"""Coordination Engine — engine koordinasi."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_coordinator import (CoordinationTask, CoordinationPlan,
                                                     CoordinationResult)


class CoordinationEngine:
    """Engine koordinasi — preview-only."""

    def __init__(self) -> None:
        self._plans: Dict[str, CoordinationPlan] = {}

    def create_plan(self, plan_id: str, tasks: List[CoordinationTask] = None) -> CoordinationPlan:
        tasks = tasks or []
        completed = sum(1 for t in tasks if t.status == "completed")
        plan = CoordinationPlan(
            plan_id=plan_id,
            tasks=tasks,
            total=len(tasks),
            completed=completed,
            is_ready=completed == len(tasks) if tasks else False,
        )
        self._plans[plan_id] = plan
        return plan

    def complete_task(self, plan_id: str, task_id: str) -> CoordinationResult:
        plan = self._plans.get(plan_id)
        if not plan:
            return CoordinationResult(f"{plan_id}/{task_id}", False, "plan not found")
        new_tasks = []
        found = False
        for t in plan.tasks:
            if t.task_id == task_id:
                new_tasks.append(CoordinationTask(t.task_id, t.subsystem, t.action,
                                                  "completed", t.order))
                found = True
            else:
                new_tasks.append(t)
        if not found:
            return CoordinationResult(f"{plan_id}/{task_id}", False, "task not found")
        completed = sum(1 for t in new_tasks if t.status == "completed")
        p2 = CoordinationPlan(
            plan_id=plan_id,
            tasks=new_tasks,
            total=plan.total,
            completed=completed,
            is_ready=completed == plan.total,
        )
        self._plans[plan_id] = p2
        return CoordinationResult(f"{plan_id}/{task_id}", True, "task completed")

    def get_plan(self, plan_id: str) -> CoordinationPlan | None:
        return self._plans.get(plan_id)

    def count(self) -> int:
        return len(self._plans)
