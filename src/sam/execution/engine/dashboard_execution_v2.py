# OP-417 — Dashboard Execution V2
# Python 3.8, frozen DTO, synchronous, presentation only

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .execution_builder import ExecutionBuilder, ExecutionPackage
from .execution_validator import ExecutionValidator
from .rollback_planner import RollbackPlanner, RollbackPlan
from .execution_scheduler import ExecutionScheduler, ExecutionQueue


@dataclass(frozen=True)
class ExecutionPackageCard:
    total_tasks: int = 0
    total_groups: int = 0
    estimated_duration_seconds: int = 0
    requires_approval: bool = True
    risk_level: str = "low"


@dataclass(frozen=True)
class TaskCard:
    total: int = 0
    pending: int = 0
    validated: int = 0
    scheduled: int = 0
    ready: int = 0
    high_risk: int = 0
    needing_approval: int = 0


@dataclass(frozen=True)
class ScheduleCard:
    total_stages: int = 0
    total_tasks: int = 0
    sequential_stages: int = 0
    parallel_stages: int = 0
    total_duration_seconds: int = 0


@dataclass(frozen=True)
class RollbackCard:
    plan_available: bool = False
    total_steps: int = 0
    requires_approval: bool = True
    partial_possible: bool = True
    estimated_duration_seconds: int = 0


@dataclass(frozen=True)
class ValidationCard:
    passed: bool = True
    errors: int = 0
    warnings: int = 0
    total_issues: int = 0


@dataclass(frozen=True)
class RiskCard:
    aggregated_level: str = "low"
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0
    requires_guardian: bool = False


@dataclass(frozen=True)
class ExecutionDashboardV2:
    package: ExecutionPackageCard = field(default_factory=ExecutionPackageCard)
    tasks: TaskCard = field(default_factory=TaskCard)
    schedule: ScheduleCard = field(default_factory=ScheduleCard)
    rollback: RollbackCard = field(default_factory=RollbackCard)
    validation: ValidationCard = field(default_factory=ValidationCard)
    risk: RiskCard = field(default_factory=RiskCard)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ExecutionDashboardV2Builder:
    """Builds execution dashboard DTOs — pure composition."""

    @staticmethod
    def build(
        pkg: ExecutionPackage,
        report: "ValidationReport",
        rollback_plan: RollbackPlan,
        queue: ExecutionQueue,
    ) -> ExecutionDashboardV2:
        package_card = ExecutionPackageCard(
            total_tasks=pkg.total_tasks,
            total_groups=pkg.total_groups,
            estimated_duration_seconds=pkg.estimated_duration_seconds,
            requires_approval=pkg.requires_approval,
            risk_level=pkg.aggregated_risk_level,
        )

        high_risk = sum(1 for t in pkg.tasks if t.risk.level in ("high", "critical"))
        needing_appr = sum(1 for t in pkg.tasks if t.requires_approval)
        task_card = TaskCard(
            total=pkg.total_tasks,
            pending=pkg.total_tasks,
            high_risk=high_risk,
            needing_approval=needing_appr,
        )

        seq = sum(1 for s in queue.stages if not s.parallel)
        par = sum(1 for s in queue.stages if s.parallel)
        schedule_card = ScheduleCard(
            total_stages=queue.total_stages,
            total_tasks=queue.total_tasks,
            sequential_stages=seq,
            parallel_stages=par,
            total_duration_seconds=queue.estimated_duration_seconds,
        )

        rollback_card = RollbackCard(
            plan_available=rollback_plan.total_steps > 0,
            total_steps=rollback_plan.total_steps,
            requires_approval=rollback_plan.requires_approval,
            partial_possible=rollback_plan.partial_rollback_possible,
            estimated_duration_seconds=rollback_plan.estimated_duration_seconds,
        )

        validation_card = ValidationCard(
            passed=report.passed,
            errors=report.errors,
            warnings=report.warnings,
            total_issues=report.total_issues,
        )

        low = sum(1 for t in pkg.tasks if t.risk.level == "low")
        med = sum(1 for t in pkg.tasks if t.risk.level == "medium")
        high = sum(1 for t in pkg.tasks if t.risk.level == "high")
        crit = sum(1 for t in pkg.tasks if t.risk.level == "critical")
        risk_card = RiskCard(
            aggregated_level=pkg.aggregated_risk_level,
            low=low, medium=med, high=high, critical=crit,
            requires_guardian=pkg.requires_guardian,
        )

        return ExecutionDashboardV2(
            package=package_card,
            tasks=task_card,
            schedule=schedule_card,
            rollback=rollback_card,
            validation=validation_card,
            risk=risk_card,
        )
