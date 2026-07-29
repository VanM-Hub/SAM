# OP-414 — Rollback Planner
# Python 3.8, frozen DTO, synchronous, no execute rollback

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .execution_task import ExecutionTask, TaskDependency, TaskStatus, TaskRisk
from .execution_builder import ExecutionPackage


@dataclass(frozen=True)
class RollbackStep:
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    task_name: str = ""
    action: str = "rollback"
    connector_type: str = ""
    target: str = ""
    risk_level: str = "high"
    order: int = 0
    description: str = ""


@dataclass(frozen=True)
class RollbackPlan:
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    steps: Tuple[RollbackStep, ...] = field(default_factory=tuple)
    total_steps: int = 0
    reverse_order: Tuple[str, ...] = field(default_factory=tuple)  # task_ids in reverse exec order
    partial_rollback_possible: bool = True
    requires_approval: bool = True
    estimated_duration_seconds: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class RollbackSummary:
    plan_available: bool = False
    total_steps: int = 0
    requires_approval: bool = True
    partial_possible: bool = True
    estimated_duration_seconds: int = 0
    notes: str = ""


class RollbackPlanner:
    """Creates rollback plans for execution packages.

    Generates reverse-ordered rollback steps.
    Does NOT execute rollback — plans only.
    """

    def plan(self, package: ExecutionPackage) -> RollbackPlan:
        """Create a rollback plan from an execution package.

        Reverse dependency order: last executed task should be rolled back first.
        """
        if not package.tasks:
            return RollbackPlan()

        steps: List[RollbackStep] = []
        reverse_order: List[str] = []

        # Sort tasks by order descending (reverse execution order)
        sorted_tasks = sorted(
            package.tasks,
            key=lambda t: (t.parallel_group, t.order),
            reverse=True,
        )

        for idx, task in enumerate(sorted_tasks):
            if not task.connector_type:
                continue

            reverse_order.append(task.task_id)

            description = f"Rollback '{task.action}' on {task.target} ({task.connector_type})"

            steps.append(RollbackStep(
                task_id=task.task_id,
                task_name=task.name,
                action=task.action,
                connector_type=task.connector_type,
                target=task.target,
                risk_level=task.risk.level if task.risk else "high",
                order=idx + 1,
                description=description,
            ))

        # Estimate duration: 1s per step
        duration = len(steps) * 2  # Rollback takes longer than forward

        return RollbackPlan(
            steps=tuple(steps),
            total_steps=len(steps),
            reverse_order=tuple(reverse_order),
            partial_rollback_possible=True,
            requires_approval=package.requires_approval,
            estimated_duration_seconds=duration,
        )

    def to_summary(self, plan: RollbackPlan) -> RollbackSummary:
        """Convert plan to summary DTO."""
        return RollbackSummary(
            plan_available=plan.total_steps > 0,
            total_steps=plan.total_steps,
            requires_approval=plan.requires_approval,
            partial_possible=plan.partial_rollback_possible,
            estimated_duration_seconds=plan.estimated_duration_seconds,
            notes=f"Rollback plan with {plan.total_steps} steps (reverse order)",
        )

    def validate_plan(self, plan: RollbackPlan,
                      package: ExecutionPackage) -> Tuple[str, ...]:
        """Validate rollback plan completeness."""
        errors: List[str] = []
        task_ids = set(t.task_id for t in package.tasks)

        if plan.total_steps == 0:
            errors.append("Rollback plan is empty")

        if plan.total_steps != len(task_ids):
            errors.append(f"Rollback steps ({plan.total_steps}) don't match tasks ({len(task_ids)})")

        for step in plan.steps:
            if step.task_id not in task_ids:
                errors.append(f"Rollback step references unknown task {step.task_id[:8]}")

        return tuple(errors)
