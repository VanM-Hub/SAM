"""
OP-277 — Operational Coordinator

Pipeline orchestration:

  Observation → Learning → Proposal → Dependency → Conflict
  → Priority → MissionPlan → Conversation DTO

Coordinator tidak boleh submit mission, hanya mengorkestrasi pipeline.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from datetime import datetime


@dataclass(frozen=True)
class OrchestrationStage:
    name: str
    status: str  # pending | running | success | failed | skipped
    duration_ms: float = 0.0
    error: str = ""
    output_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "output_summary": self.output_summary,
        }


@dataclass(frozen=True)
class OrchestrationResult:
    pipeline_id: str
    started_at: str
    completed_at: str
    stages: tuple[OrchestrationStage, ...]
    dependency_graph_dto: Any = None
    conflict_report: Any = None
    priority_plan: Any = None
    mission_plan: Any = None
    escalation_plan: Any = None
    workload_snapshot: Any = None
    total_duration_ms: float = 0.0
    success: bool = True

    @property
    def failed_stages(self) -> list[OrchestrationStage]:
        return [s for s in self.stages if s.status == "failed"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline_id": self.pipeline_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "success": self.success,
            "total_duration_ms": self.total_duration_ms,
            "stages": [s.to_dict() for s in self.stages],
        }


class OperationalCoordinator:
    """
    Orchestrator untuk pipeline mission planning.

    Menjalankan stage secara berurutan.
    Jika suatu stage gagal, stage berikutnya di-skip.
    Coordinator tidak submit mission — hanya merencanakan.
    """

    def __init__(self, name: str = "coordinator") -> None:
        self._name = name

    def orchestrate(self,
                    proposals: list[dict[str, Any]],
                    dependency_graph: Any = None,
                    conflict_detector: Any = None,
                    priority_optimizer: Any = None,
                    mission_planner: Any = None,
                    escalation_planner: Any = None,
                    workload_balancer: Any = None,
                    approvals: list[dict[str, Any]] | None = None,
                    missions: list[dict[str, Any]] | None = None,
                    locks: list[dict[str, Any]] | None = None,
                    schedules: list[dict[str, Any]] | None = None,
                    ) -> OrchestrationResult:
        """
        Run full orchestration pipeline.
        """
        import time
        pid = f"pipe_{int(datetime.now().timestamp())}"
        start = time.time()
        started_at = datetime.now().isoformat(timespec="seconds")

        stages: list[OrchestrationStage] = []
        dto_dep_graph = None
        conflict_report = None
        priority_plan = None
        mission_plan = None
        escalation_plan = None
        workload_snapshot = None
        success = True

        # Stage 1: Build Dependency Graph
        if dependency_graph:
            s = self._run_stage("dependency_graph", lambda: self._stage_dep_graph(
                dependency_graph, proposals))
            stages.append(s)
            if s.status == "success":
                dto_dep_graph = dependency_graph.to_dto()

        # Stage 2: Detect Conflicts
        if conflict_detector:
            s = self._run_stage("conflict_detection", lambda: self._stage_conflict(
                conflict_detector, proposals, missions, locks, approvals, schedules))
            stages.append(s)
            if s.status == "success":
                conflict_report = s.output_summary

        # Stage 3: Optimize Priority
        if priority_optimizer:
            s = self._run_stage("priority_optimization", lambda: self._stage_priority(
                priority_optimizer, proposals))
            stages.append(s)
            if s.status == "success":
                priority_plan = s.output_summary

        # Stage 4: Build Mission Plan
        if mission_planner:
            s = self._run_stage("mission_planning", lambda: self._stage_mission(
                mission_planner, proposals))
            stages.append(s)
            if s.status == "success":
                mission_plan = s.output_summary

        # Stage 5: Escalation Plan
        if escalation_planner:
            s = self._run_stage("escalation_planning", lambda: self._stage_escalation(
                escalation_planner, approvals))
            stages.append(s)
            if s.status == "success":
                escalation_plan = s.output_summary

        # Stage 6: Workload Snapshot
        if workload_balancer:
            s = self._run_stage("workload", lambda: self._stage_workload(
                workload_balancer, approvals, missions, proposals))
            stages.append(s)
            if s.status == "success":
                workload_snapshot = s.output_summary

        completed_at = datetime.now().isoformat(timespec="seconds")
        total_ms = round((time.time() - start) * 1000, 2)
        success = all(s.status != "failed" for s in stages)

        return OrchestrationResult(
            pipeline_id=pid,
            started_at=started_at,
            completed_at=completed_at,
            stages=tuple(stages),
            dependency_graph_dto=dto_dep_graph,
            conflict_report=conflict_report,
            priority_plan=priority_plan,
            mission_plan=mission_plan,
            escalation_plan=escalation_plan,
            workload_snapshot=workload_snapshot,
            total_duration_ms=total_ms,
            success=success,
        )

    def _run_stage(self, name: str, fn: Callable) -> OrchestrationStage:
        import time
        start = time.time()
        try:
            result = fn()
            dur = round((time.time() - start) * 1000, 2)
            summary = str(result)[:200] if result else "completed"
            return OrchestrationStage(
                name=name, status="success", duration_ms=dur,
                output_summary=summary,
            )
        except Exception as e:
            dur = round((time.time() - start) * 1000, 2)
            return OrchestrationStage(
                name=name, status="failed", duration_ms=dur,
                error=str(e),
            )

    def _stage_dep_graph(self, dep_graph, proposals: list[dict[str, Any]]) -> str:
        dep_graph.add_from_proposals(proposals)
        dto = dep_graph.to_dto()
        return f"{dto.node_count} nodes, {dto.edge_count} edges, " \
               f"cycle={dto.has_cycle}"

    def _stage_conflict(self, detector, proposals, missions, locks, approvals, schedules) -> str:
        report = detector.detect(
            proposals=proposals,
            missions=missions,
            locks=locks,
            approvals=approvals,
            schedules=schedules,
        )
        return f"{report.total} conflicts ({report.critical_count} critical, " \
               f"{report.high_count} high)"

    def _stage_priority(self, optimizer, proposals: list[dict[str, Any]]) -> str:
        plan = optimizer.optimize(proposals)
        return f"{plan.total_items} items scored, " \
               f"top: {plan.highest_score}, avg: {plan.average_score}"

    def _stage_mission(self, planner, proposals: list[dict[str, Any]]) -> str:
        plan = planner.plan(proposals)
        return f"{plan.total_steps} steps, {plan.total_estimated_minutes} min, " \
               f"{plan.total_approvals_needed} approvals"

    def _stage_escalation(self, planner, approvals) -> str:
        if not approvals:
            return "no pending approvals"
        plan = planner.plan(approvals)
        return f"{plan.total} escalations " \
               f"({plan.reminder_count} reminders, {plan.expired_count} expired)"

    def _stage_workload(self, balancer, approvals, missions, proposals) -> str:
        snap = balancer.snapshot(
            approvals=approvals,
            missions=missions,
            proposals=proposals,
        )
        return f"pending: {snap.total_pending_approvals} approvals, " \
               f"{snap.total_pending_missions} missions, " \
               f"health: {snap.health_status}"
