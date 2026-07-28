"""
OP-279 — Dashboard DTO untuk Orchestration Layer

DTO:
  - MissionPlanSummary
  - ConflictSummary
  - DependencyGraphSummary
  - PriorityListSummary
  - WorkloadSummary
  - EscalationQueueSummary
  - PlanningHealthDTO

Pure data — tidak ada rendering, tidak ada business logic.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass(frozen=True)
class StepSummary:
    proposal_id: str
    title: str
    priority_score: float
    severity: str
    has_blockers: bool = False
    estimated_minutes: float = 30.0
    dependency_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "title": self.title,
            "priority_score": self.priority_score,
            "severity": self.severity,
            "has_blockers": self.has_blockers,
            "estimated_minutes": self.estimated_minutes,
            "dependency_count": self.dependency_count,
        }


@dataclass(frozen=True)
class MissionPlanSummary:
    plan_id: str
    name: str
    total_steps: int
    total_estimated_minutes: float
    total_approvals_needed: int
    critical_count: int
    blocker_count: int
    steps: tuple[StepSummary, ...]
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "name": self.name,
            "total_steps": self.total_steps,
            "total_estimated_minutes": self.total_estimated_minutes,
            "total_approvals_needed": self.total_approvals_needed,
            "critical_count": self.critical_count,
            "blocker_count": self.blocker_count,
            "created_at": self.created_at,
            "steps": [s.to_dict() for s in self.steps],
        }


@dataclass(frozen=True)
class ConflictSummary:
    total: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    by_kind: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "by_kind": self.by_kind,
        }


@dataclass(frozen=True)
class DependencyGraphSummary:
    node_count: int
    edge_count: int
    root_count: int
    leaf_count: int
    has_cycle: bool
    execution_order_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "root_count": self.root_count,
            "leaf_count": self.leaf_count,
            "has_cycle": self.has_cycle,
            "execution_order_count": self.execution_order_count,
        }


@dataclass(frozen=True)
class PriorityItemSummary:
    proposal_id: str
    rank: int
    score: float
    top_factor: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "rank": self.rank,
            "score": self.score,
            "top_factor": self.top_factor,
        }


@dataclass(frozen=True)
class PriorityListSummary:
    total_items: int
    highest_score: float
    lowest_score: float
    average_score: float
    top_3: tuple[PriorityItemSummary, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_items": self.total_items,
            "highest_score": self.highest_score,
            "lowest_score": self.lowest_score,
            "average_score": self.average_score,
            "top_3": [t.to_dict() for t in self.top_3],
        }


@dataclass(frozen=True)
class WorkloadSummary:
    total_pending_approvals: int
    total_pending_missions: int
    total_proposals: int
    critical_approval_count: int
    stalled_proposals: int
    avg_pending_per_approver: float
    max_pending_per_approver: int
    health_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_pending_approvals": self.total_pending_approvals,
            "total_pending_missions": self.total_pending_missions,
            "total_proposals": self.total_proposals,
            "critical_approval_count": self.critical_approval_count,
            "stalled_proposals": self.stalled_proposals,
            "avg_pending_per_approver": self.avg_pending_per_approver,
            "max_pending_per_approver": self.max_pending_per_approver,
            "health_status": self.health_status,
        }


@dataclass(frozen=True)
class EscalationQueueSummary:
    total: int
    reminder_count: int
    escalation_count: int
    critical_count: int
    expired_count: int
    oldest_days: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "reminder_count": self.reminder_count,
            "escalation_count": self.escalation_count,
            "critical_count": self.critical_count,
            "expired_count": self.expired_count,
            "oldest_days": self.oldest_days,
        }


@dataclass(frozen=True)
class PlanningHealthDTO:
    healthy: bool
    plan_ready: bool = False
    has_conflicts: bool = False
    has_cycle: bool = False
    workload_healthy: bool = True
    active_escalations: int = 0
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "healthy": self.healthy,
            "plan_ready": self.plan_ready,
            "has_conflicts": self.has_conflicts,
            "has_cycle": self.has_cycle,
            "workload_healthy": self.workload_healthy,
            "active_escalations": self.active_escalations,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


class OrchestratorDashboardBuilder:
    """
    Build orchestration DTOs from module outputs.
    """

    def build_plan_summary(self, mission_plan: Any) -> MissionPlanSummary:
        steps = getattr(mission_plan, 'steps', ())
        return MissionPlanSummary(
            plan_id=getattr(mission_plan, 'plan_id', ''),
            name=getattr(mission_plan, 'name', ''),
            total_steps=getattr(mission_plan, 'total_steps', 0),
            total_estimated_minutes=getattr(mission_plan, 'total_estimated_minutes', 0),
            total_approvals_needed=getattr(mission_plan, 'total_approvals_needed', 0),
            critical_count=getattr(mission_plan, 'critical_count', 0),
            blocker_count=getattr(mission_plan, 'blocker_count', 0),
            steps=tuple(
                StepSummary(
                    proposal_id=s.proposal_id,
                    title=getattr(s, 'title', ''),
                    priority_score=getattr(s, 'priority_score', 0),
                    severity=getattr(s, 'severity', 'medium'),
                    has_blockers=bool(getattr(s, 'blockers', ())),
                    estimated_minutes=getattr(s, 'estimated_minutes', 30),
                    dependency_count=len(getattr(s, 'dependencies', ())),
                ) for s in steps
            ),
            created_at=getattr(mission_plan, 'created_at', ''),
        )

    def build_conflict_summary(self, conflict_report: Any) -> ConflictSummary:
        if not conflict_report:
            return ConflictSummary(total=0, critical_count=0, high_count=0,
                                   medium_count=0, low_count=0)
        conflicts = getattr(conflict_report, 'conflicts', ())
        by_kind: dict[str, int] = {}
        for c in conflicts:
            k = c.kind.value if hasattr(c.kind, 'value') else str(c.kind)
            by_kind[k] = by_kind.get(k, 0) + 1
        return ConflictSummary(
            total=getattr(conflict_report, 'total', len(conflicts)),
            critical_count=getattr(conflict_report, 'critical_count', 0),
            high_count=getattr(conflict_report, 'high_count', 0),
            medium_count=getattr(conflict_report, 'medium_count', 0),
            low_count=getattr(conflict_report, 'low_count', 0),
            by_kind=by_kind,
        )

    def build_dep_graph_summary(self, dto: Any) -> DependencyGraphSummary:
        if not dto:
            return DependencyGraphSummary(
                node_count=0, edge_count=0, root_count=0,
                leaf_count=0, has_cycle=False, execution_order_count=0)
        return DependencyGraphSummary(
            node_count=getattr(dto, 'node_count', 0),
            edge_count=getattr(dto, 'edge_count', 0),
            root_count=len(getattr(dto, 'roots', ())),
            leaf_count=len(getattr(dto, 'leaves', ())),
            has_cycle=getattr(dto, 'has_cycle', False),
            execution_order_count=len(getattr(dto, 'execution_order', ())),
        )

    def build_priority_summary(self, priority_plan: Any) -> PriorityListSummary:
        if not priority_plan:
            return PriorityListSummary(
                total_items=0, highest_score=0, lowest_score=0, average_score=0)
        items = getattr(priority_plan, 'items', ())
        top_3 = tuple(
            PriorityItemSummary(
                proposal_id=i.proposal_id,
                rank=i.rank,
                score=i.score,
                top_factor=max(i.factors, key=i.factors.get) if i.factors else "",
            ) for i in items[:3]
        )
        return PriorityListSummary(
            total_items=getattr(priority_plan, 'total_items', len(items)),
            highest_score=getattr(priority_plan, 'highest_score', 0),
            lowest_score=getattr(priority_plan, 'lowest_score', 0),
            average_score=getattr(priority_plan, 'average_score', 0),
            top_3=top_3,
        )

    def build_workload_summary(self, workload_snapshot: Any) -> WorkloadSummary:
        if not workload_snapshot:
            return WorkloadSummary(
                total_pending_approvals=0, total_pending_missions=0,
                total_proposals=0, critical_approval_count=0,
                stalled_proposals=0, avg_pending_per_approver=0,
                max_pending_per_approver=0, health_status="unknown")
        return WorkloadSummary(
            total_pending_approvals=getattr(workload_snapshot, 'total_pending_approvals', 0),
            total_pending_missions=getattr(workload_snapshot, 'total_pending_missions', 0),
            total_proposals=getattr(workload_snapshot, 'total_proposals', 0),
            critical_approval_count=getattr(workload_snapshot, 'critical_approval_count', 0),
            stalled_proposals=getattr(workload_snapshot, 'stalled_proposals', 0),
            avg_pending_per_approver=getattr(workload_snapshot, 'avg_pending_per_approver', 0),
            max_pending_per_approver=getattr(workload_snapshot, 'max_pending_per_approver', 0),
            health_status=getattr(workload_snapshot, 'health_status', 'unknown'),
        )

    def build_escalation_summary(self, escalation_plan: Any) -> EscalationQueueSummary:
        if not escalation_plan:
            return EscalationQueueSummary(
                total=0, reminder_count=0, escalation_count=0,
                critical_count=0, expired_count=0)
        return EscalationQueueSummary(
            total=getattr(escalation_plan, 'total', 0),
            reminder_count=getattr(escalation_plan, 'reminder_count', 0),
            escalation_count=getattr(escalation_plan, 'escalation_count', 0),
            critical_count=getattr(escalation_plan, 'critical_count', 0),
            expired_count=getattr(escalation_plan, 'expired_count', 0),
        )

    def build_health(self, mission_plan: Any = None,
                     conflict_report: Any = None,
                     dep_graph: Any = None,
                     workload: Any = None,
                     escalation: Any = None) -> PlanningHealthDTO:
        warnings: list[str] = []
        errors: list[str] = []

        has_cycle = getattr(dep_graph, 'has_cycle', False) if dep_graph else False
        has_conflicts = getattr(conflict_report, 'total', 0) > 0 if conflict_report else False
        plan_ready = getattr(mission_plan, 'total_steps', 0) > 0 if mission_plan else False
        workload_healthy = getattr(workload, 'health_status', 'healthy') != 'overloaded' if workload else True
        escalations = getattr(escalation, 'total', 0) if escalation else 0

        if has_cycle:
            errors.append("Dependency graph memiliki cycle")
        if has_conflicts:
            warnings.append(f"{getattr(conflict_report, 'total', 0)} konflik terdeteksi")
        if not workload_healthy:
            warnings.append("Workload overloaded")
        if escalations > 5:
            warnings.append(f"{escalations} eskalasi aktif")

        healthy = len(errors) == 0 and len(warnings) == 0

        return PlanningHealthDTO(
            healthy=healthy,
            plan_ready=plan_ready,
            has_conflicts=has_conflicts,
            has_cycle=has_cycle,
            workload_healthy=workload_healthy,
            active_escalations=escalations,
            warnings=tuple(warnings),
            errors=tuple(errors),
        )
