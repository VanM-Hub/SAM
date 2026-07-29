# OP-416 — Conversation Execution V2
# Python 3.8, frozen DTO, synchronous, read-only queries

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from .execution_builder import ExecutionBuilder, ExecutionPackage
from .execution_validator import ExecutionValidator, ValidationReport
from .rollback_planner import RollbackPlanner, RollbackPlan, RollbackSummary
from .execution_scheduler import ExecutionScheduler, ExecutionQueue, ScheduleSummary


@dataclass(frozen=True)
class ExecutionQueryResultV2:
    query_type: str = ""
    data: Any = None
    count: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConversationExecutionV2Bridge:
    """Read-only query bridge for Execution Engine V2.

    Queries:
    - execution package
    - execution tasks
    - dependency graph
    - rollback
    - validation
    - schedule
    - estimated duration
    - risk summary
    - approval state
    - readiness
    """

    def __init__(
        self,
        builder: ExecutionBuilder,
        validator: ExecutionValidator,
        rollback_planner: RollbackPlanner,
        scheduler: ExecutionScheduler,
    ) -> None:
        self._builder = builder
        self._validator = validator
        self._rollback_planner = rollback_planner
        self._scheduler = scheduler

    def query(self, query_type: str,
              params: Optional[Dict[str, Any]] = None) -> ExecutionQueryResultV2:
        params = params or {}
        handlers = {
            "execution package": self._query_package,
            "execution tasks": self._query_tasks,
            "dependency graph": self._query_dependency_graph,
            "rollback": self._query_rollback,
            "validation": self._query_validation,
            "schedule": self._query_schedule,
            "estimated duration": self._query_duration,
            "risk summary": self._query_risk,
            "approval state": self._query_approval,
            "readiness": self._query_readiness,
        }
        handler = handlers.get(query_type.lower())
        if handler is None:
            return ExecutionQueryResultV2(
                query_type=query_type,
                data={"error": f"Unknown query type: {query_type}"},
                count=0,
            )
        return handler(params)

    def _get_package(self, params: Dict[str, Any]) -> ExecutionPackage:
        from sam.execution.execution_request import ExecutionPlan, ExecutionRequest
        requests = tuple(
            ExecutionRequest(
                connector_type=params.get("connector_type", "file"),
                action=params.get("action", "read"),
            )
            for _ in range(params.get("request_count", 1))
        )
        plan = ExecutionPlan(requests=requests)
        return self._builder.build(plan)

    def _query_package(self, params: Dict[str, Any]) -> ExecutionQueryResultV2:
        pkg = self._get_package(params)
        data = {
            "package_id": pkg.package_id[:8],
            "plan_id": pkg.plan_id[:8],
            "total_tasks": pkg.total_tasks,
            "total_groups": pkg.total_groups,
            "estimated_duration": pkg.estimated_duration_seconds,
            "requires_approval": pkg.requires_approval,
            "risk_level": pkg.aggregated_risk_level,
        }
        return ExecutionQueryResultV2(
            query_type="execution package", data=data, count=pkg.total_tasks,
        )

    def _query_tasks(self, params: Dict[str, Any]) -> ExecutionQueryResultV2:
        pkg = self._get_package(params)
        tasks_data = [
            {
                "id": t.task_id[:8],
                "name": t.name,
                "action": t.action,
                "target": t.target,
                "risk": t.risk.level if t.risk else "low",
                "requires_approval": t.requires_approval,
                "group": t.parallel_group,
                "order": t.order,
            }
            for t in pkg.tasks[:20]
        ]
        return ExecutionQueryResultV2(
            query_type="execution tasks", data={"tasks": tasks_data},
            count=len(pkg.tasks),
        )

    def _query_dependency_graph(self, params: Dict[str, Any]) -> ExecutionQueryResultV2:
        pkg = self._get_package(params)
        edges = []
        for t in pkg.tasks[:10]:
            for d in t.dependencies:
                edges.append({
                    "from": d.depends_on[:8] if d.depends_on else "",
                    "to": t.task_id[:8],
                    "condition": d.condition,
                })
        return ExecutionQueryResultV2(
            query_type="dependency graph", data={"edges": edges}, count=len(edges),
        )

    def _query_rollback(self, params: Dict[str, Any]) -> ExecutionQueryResultV2:
        pkg = self._get_package(params)
        rp = self._rollback_planner.plan(pkg)
        summary = self._rollback_planner.to_summary(rp)
        data = {
            "available": summary.plan_available,
            "total_steps": summary.total_steps,
            "requires_approval": summary.requires_approval,
            "partial_possible": summary.partial_possible,
            "estimated_duration": summary.estimated_duration_seconds,
            "steps": [
                {"task": s.task_name[:20], "action": s.action, "order": s.order}
                for s in rp.steps[:10]
            ],
        }
        return ExecutionQueryResultV2(
            query_type="rollback", data=data, count=rp.total_steps,
        )

    def _query_validation(self, params: Dict[str, Any]) -> ExecutionQueryResultV2:
        pkg = self._get_package(params)
        report = self._validator.validate(pkg)
        data = {
            "passed": report.passed,
            "errors": report.errors,
            "warnings": report.warnings,
            "total_issues": report.total_issues,
            "issues": [
                {"category": i.category, "severity": i.severity.value, "message": i.message}
                for i in report.issues[:10]
            ],
        }
        return ExecutionQueryResultV2(
            query_type="validation", data=data, count=report.total_issues,
        )

    def _query_schedule(self, params: Dict[str, Any]) -> ExecutionQueryResultV2:
        pkg = self._get_package(params)
        queue = self._scheduler.schedule(pkg)
        summary = self._scheduler.to_summary(queue)
        data = {
            "stages": queue.total_stages,
            "tasks": summary.total_tasks,
            "parallel_groups": summary.parallel_groups,
            "estimated_duration": summary.estimated_duration_seconds,
            "stages_detail": [
                {"name": s.name, "tasks": len(s.tasks), "parallel": s.parallel,
                 "duration": s.estimated_duration_seconds}
                for s in queue.stages[:5]
            ],
        }
        return ExecutionQueryResultV2(
            query_type="schedule", data=data, count=queue.total_stages,
        )

    def _query_duration(self, params: Dict[str, Any]) -> ExecutionQueryResultV2:
        pkg = self._get_package(params)
        data = {
            "estimated_seconds": pkg.estimated_duration_seconds,
            "estimated_human": f"{pkg.estimated_duration_seconds}s",
            "total_tasks": pkg.total_tasks,
        }
        return ExecutionQueryResultV2(
            query_type="estimated duration", data=data, count=1,
        )

    def _query_risk(self, params: Dict[str, Any]) -> ExecutionQueryResultV2:
        pkg = self._get_package(params)
        risk_levels = {}
        for t in pkg.tasks:
            level = t.risk.level if t.risk else "low"
            risk_levels[level] = risk_levels.get(level, 0) + 1
        data = {
            "aggregated_risk": pkg.aggregated_risk_level,
            "by_level": risk_levels,
            "requires_guardian": pkg.requires_guardian,
        }
        return ExecutionQueryResultV2(
            query_type="risk summary", data=data, count=len(pkg.tasks),
        )

    def _query_approval(self, params: Dict[str, Any]) -> ExecutionQueryResultV2:
        pkg = self._get_package(params)
        tasks_needing_approval = [
            {"name": t.name, "risk": t.risk.level if t.risk else "low"}
            for t in pkg.tasks if t.requires_approval
        ]
        data = {
            "approval_required": pkg.requires_approval,
            "tasks_needing_approval": len(tasks_needing_approval),
            "tasks": tasks_needing_approval[:10],
        }
        return ExecutionQueryResultV2(
            query_type="approval state", data=data, count=len(tasks_needing_approval),
        )

    def _query_readiness(self, params: Dict[str, Any]) -> ExecutionQueryResultV2:
        pkg = self._get_package(params)
        report = self._validator.validate(pkg)
        validated = report.passed
        has_schedule = pkg.total_tasks > 0
        ready = validated and has_schedule and not pkg.requires_approval

        data = {
            "ready": ready,
            "validated": validated,
            "has_tasks": has_schedule,
            "needs_approval": pkg.requires_approval,
            "total_tasks": pkg.total_tasks,
        }
        return ExecutionQueryResultV2(
            query_type="readiness", data=data, count=1,
        )
