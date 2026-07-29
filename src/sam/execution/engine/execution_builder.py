# OP-412 — Execution Builder
# Python 3.8, frozen DTO, synchronous
# Converts ExecutionPlan → ExecutionPackage with task decomposition

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from sam.execution.execution_request import (
    ExecutionPlan, ExecutionRequest, ExecutionStatus, ExecutionRisk,
)

from .execution_task import (
    ExecutionTask, TaskGroup, TaskDependency, TaskCondition,
    TaskResult, TaskStatus, TaskRisk, TaskMetadata,
)


@dataclass(frozen=True)
class ExecutionPackage:
    package_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str = ""
    tasks: Tuple[ExecutionTask, ...] = field(default_factory=tuple)
    groups: Tuple[TaskGroup, ...] = field(default_factory=tuple)
    total_tasks: int = 0
    total_groups: int = 0
    estimated_duration_seconds: int = 0
    requires_approval: bool = True
    requires_guardian: bool = False
    aggregated_risk_level: str = "low"
    created_at: datetime = field(default_factory=datetime.utcnow)


class ExecutionBuilder:
    """Builds an ExecutionPackage from an ExecutionPlan.

    Decomposes plan into tasks, creates dependency graph,
    parallel groups, and assigns rollback markers.
    """

    def build(self, plan: ExecutionPlan) -> ExecutionPackage:
        """Convert an ExecutionPlan into an ExecutionPackage."""
        if not plan.requests:
            return ExecutionPackage(
                plan_id=plan.plan_id,
                total_tasks=0,
                requires_approval=False,
            )

        tasks: List[ExecutionTask] = []
        group_map: Dict[int, List[ExecutionTask]] = {}
        task_index: Dict[str, int] = {}

        for i, req in enumerate(plan.requests):
            # Determine risk
            req_risk = req.risk
            task_risk = TaskRisk(
                level=req_risk.level if req_risk else "low",
                score=req_risk.score if req_risk else 0.0,
                factors=req_risk.factors if req_risk else (),
                description=req_risk.description if req_risk else "",
            )

            # Determine parallel group from plan
            pgroup = self._find_parallel_group(plan, req.request_id)

            # Determine dependencies
            deps: List[TaskDependency] = []
            dep_idx = 0
            for other_req in plan.requests:
                if other_req.request_id == req.request_id:
                    continue
                is_before = False
                if plan.dependency_order:
                    try:
                        req_pos = plan.dependency_order.index(req.request_id)
                        other_pos = plan.dependency_order.index(other_req.request_id)
                        is_before = other_pos < req_pos
                    except ValueError:
                        pass
                if is_before:
                    deps.append(TaskDependency(
                        depends_on=other_req.request_id,
                        condition="success",
                        required=True,
                    ))
                    dep_idx += 1

            # Create metadata
            target_name = req.target.name if req.target else ""
            meta = TaskMetadata(
                source="execution_plan",
                connector_type=req.connector_type,
                action=req.action,
                target_name=target_name,
            )

            task = ExecutionTask(
                name=f"{req.connector_type}.{req.action}",
                description=req.description or f"{req.action} on {target_name}",
                connector_type=req.connector_type,
                action=req.action,
                target=target_name,
                risk=task_risk,
                dependencies=tuple(deps),
                metadata=meta,
                estimated_duration_seconds=1,
                requires_approval=req.requires_human_approval,
                requires_guardian=req.requires_guardian or req_risk.requires_guardian,
                parallel_group=pgroup,
                order=i + 1,
            )
            tasks.append(task)
            task_index[req.request_id] = i
            group_map.setdefault(pgroup, []).append(task)

        # Build groups
        groups: List[TaskGroup] = []
        for gid in sorted(group_map.keys()):
            group_tasks = tuple(group_map[gid])
            duration = max((t.estimated_duration_seconds for t in group_tasks), default=0)
            groups.append(TaskGroup(
                name=f"Group {gid}",
                tasks=group_tasks,
                parallel=gid > 0,
                estimated_duration_seconds=duration,
            ))

        # Aggregate risk
        risk_levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        max_risk = max((risk_levels.get(t.risk.level, 0) for t in tasks), default=0)
        reverse_map = {v: k for k, v in risk_levels.items()}
        agg_risk = reverse_map.get(max_risk, "low")

        requires_guardian = any(t.requires_guardian for t in tasks)
        total_duration = sum(
            g.estimated_duration_seconds for g in groups
        )

        return ExecutionPackage(
            plan_id=plan.plan_id,
            tasks=tuple(tasks),
            groups=tuple(groups),
            total_tasks=len(tasks),
            total_groups=len(groups),
            estimated_duration_seconds=total_duration,
            requires_approval=any(t.requires_approval for t in tasks),
            requires_guardian=requires_guardian,
            aggregated_risk_level=agg_risk,
        )

    @staticmethod
    def _find_parallel_group(plan: ExecutionPlan, request_id: str) -> int:
        """Find which parallel group a request belongs to."""
        for gidx, group in enumerate(plan.parallel_groups):
            if request_id in group:
                return gidx
        return 0
