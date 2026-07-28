"""
OP-278 — Conversation Integration

Query types baru untuk orchestration layer:
  - What should happen first?
  - What blocks this proposal?
  - Show mission plan.
  - Show dependency graph.
  - Why this priority?
  - Show conflicts.
  - Show workload.
  - Show blockers.

DTO only — tidak mengubah Conversation API yang existing.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


class QueryType:
    FIRST_PRIORITY = "first_priority"
    BLOCKERS = "blockers"
    MISSION_PLAN = "mission_plan"
    DEPENDENCY_GRAPH = "dependency_graph"
    PRIORITY_REASON = "priority_reason"
    CONFLICTS = "conflicts"
    WORKLOAD = "workload"
    ESCALATION = "escalation"


@dataclass(frozen=True)
class OrchestrationQuery:
    query_type: str
    proposal_id: str | None = None
    plan_id: str | None = None
    filters: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_type": self.query_type,
            "proposal_id": self.proposal_id,
            "plan_id": self.plan_id,
            "filters": self.filters,
            "timestamp": self.timestamp or datetime.now().isoformat(timespec="seconds"),
        }


@dataclass(frozen=True)
class OrchestrationAnswer:
    query_type: str
    answer: str
    data: Any = None
    timestamp: str = ""
    source: str = "orchestrator"

    def to_dict(self) -> dict[str, Any]:
        return {
            "query_type": self.query_type,
            "answer": self.answer,
            "data": self.data,
            "timestamp": self.timestamp or datetime.now().isoformat(timespec="seconds"),
            "source": self.source,
        }


class OrchestrationConversation:
    """
    Conversation bridge untuk orchestration queries.

    Menerima OrchestrationQuery dan menghasilkan OrchestrationAnswer.
    Semua data via DTO, tidak mengubah Conversation API existing.
    """

    def answer(self, query: OrchestrationQuery,
               coordinator_result: Any = None,
               dependency_graph: Any = None,
               conflict_report: Any = None,
               priority_plan: Any = None,
               mission_plan: Any = None,
               escalation_plan: Any = None,
               workload_snapshot: Any = None,
               ) -> OrchestrationAnswer:
        """Route query to appropriate handler."""

        handlers = {
            QueryType.FIRST_PRIORITY: self._answer_first_priority,
            QueryType.BLOCKERS: self._answer_blockers,
            QueryType.MISSION_PLAN: self._answer_mission_plan,
            QueryType.DEPENDENCY_GRAPH: self._answer_dependency_graph,
            QueryType.PRIORITY_REASON: self._answer_priority_reason,
            QueryType.CONFLICTS: self._answer_conflicts,
            QueryType.WORKLOAD: self._answer_workload,
            QueryType.ESCALATION: self._answer_escalation,
        }

        handler = handlers.get(query.query_type)
        if not handler:
            return OrchestrationAnswer(
                query_type=query.query_type,
                answer=f"Unknown query type: {query.query_type}",
                timestamp=datetime.now().isoformat(timespec="seconds"),
            )

        return handler(query, coordinator_result, dependency_graph,
                       conflict_report, priority_plan, mission_plan,
                       escalation_plan, workload_snapshot)

    def _answer_first_priority(self, query, coord, dep_graph, conflict,
                                priority, mission, escalation, workload) -> OrchestrationAnswer:
        if priority and hasattr(priority, 'items') and priority.items:
            top = priority.items[0]
            answer = (f"Prioritas pertama: **{top.proposal_id}** "
                      f"(score: {top.score})")
            if top.reason:
                answer += f"\nAlasan: {top.reason}"
            return OrchestrationAnswer(
                query_type=query.query_type, answer=answer, data=top.to_dict())
        return OrchestrationAnswer(
            query_type=query.query_type,
            answer="Tidak ada proposal untuk diprioritaskan.")

    def _answer_blockers(self, query, coord, dep_graph, conflict,
                          priority, mission, escalation, workload) -> OrchestrationAnswer:
        pid = query.proposal_id
        if not pid:
            return OrchestrationAnswer(
                query_type=query.query_type,
                answer="Sebutkan proposal_id untuk melihat blocker.")
        blockers = []
        if dep_graph and hasattr(dep_graph, 'blocked_by'):
            blockers = dep_graph.blocked_by(pid)
        if not blockers:
            answer = f"Tidak ada blocker untuk proposal **{pid}**."
        else:
            names = [b.label or b.id for b in blockers]
            answer = f"Blocker untuk **{pid}**:\n" + "\n".join(f"- {n}" for n in names)
        return OrchestrationAnswer(
            query_type=query.query_type, answer=answer,
            data=[b.id for b in blockers])

    def _answer_mission_plan(self, query, coord, dep_graph, conflict,
                              priority, mission, escalation, workload) -> OrchestrationAnswer:
        if not mission:
            return OrchestrationAnswer(
                query_type=query.query_type,
                answer="Belum ada mission plan.")
        plan_name = getattr(mission, 'name', 'Mission Plan')
        steps = getattr(mission, 'steps', ())
        answer = f"**{plan_name}** — {len(steps)} langkah\n"
        for s in steps:
            deps = f" (depends on: {', '.join(s.dependencies)})" if s.dependencies else ""
            answer += f"{s.rank if hasattr(s,'rank') else ''}. {s.proposal_id}{deps}\n"
        return OrchestrationAnswer(
            query_type=query.query_type, answer=answer,
            data=mission.to_dict() if hasattr(mission, 'to_dict') else None)

    def _answer_dependency_graph(self, query, coord, dep_graph, conflict,
                                  priority, mission, escalation, workload) -> OrchestrationAnswer:
        if not dep_graph:
            return OrchestrationAnswer(
                query_type=query.query_type,
                answer="Belum ada dependency graph.")
        dto = dep_graph.to_dto() if hasattr(dep_graph, 'to_dto') else None
        if dto:
            answer = (f"Dependency Graph: {dto.node_count} node, {dto.edge_count} edge\n"
                      f"Roots: {len(dto.roots)}, Leaves: {len(dto.leaves)}\n"
                      f"Cycle: {'⚠️ YES' if dto.has_cycle else '✅ No'}")
            if dto.execution_order:
                answer += "\nExecution order:\n" + "\n".join(f"  {i+1}. {nid}"
                            for i, nid in enumerate(dto.execution_order))
        else:
            answer = "Dependency graph tersedia."
        return OrchestrationAnswer(
            query_type=query.query_type, answer=answer, data=dto)

    def _answer_priority_reason(self, query, coord, dep_graph, conflict,
                                 priority, mission, escalation, workload) -> OrchestrationAnswer:
        pid = query.proposal_id
        if not pid or not priority:
            return OrchestrationAnswer(
                query_type=query.query_type,
                answer="Sebutkan proposal_id untuk melihat alasan prioritas.")
        item = priority.by_proposal_id(pid) if hasattr(priority, 'by_proposal_id') else None
        if not item:
            return OrchestrationAnswer(
                query_type=query.query_type,
                answer=f"Proposal **{pid}** tidak ditemukan di priority plan.")
        answer = (f"Prioritas **{pid}**: rank #{item.rank}, score {item.score}\n"
                  f"Faktor: " + ", ".join(f"{k}={v}" for k, v in item.factors.items()) + "\n"
                  f"Alasan: {item.reason}")
        return OrchestrationAnswer(
            query_type=query.query_type, answer=answer, data=item.to_dict())

    def _answer_conflicts(self, query, coord, dep_graph, conflict,
                           priority, mission, escalation, workload) -> OrchestrationAnswer:
        if not conflict:
            return OrchestrationAnswer(
                query_type=query.query_type,
                answer="Tidak ada conflict report.")
        total = getattr(conflict, 'total', 0)
        if total == 0:
            answer = "✅ Tidak ada konflik terdeteksi."
        else:
            kinds = {}
            for c in getattr(conflict, 'conflicts', ()):
                k = getattr(c, 'kind', 'unknown')
                kinds[k.value if hasattr(k, 'value') else str(k)] = \
                    kinds.get(k.value if hasattr(k, 'value') else str(k), 0) + 1
            answer = f"⚠️ {total} konflik terdeteksi:\n"
            for kind, count in kinds.items():
                answer += f"- {kind}: {count}\n"
        return OrchestrationAnswer(
            query_type=query.query_type, answer=answer,
            data=conflict.to_dict() if hasattr(conflict, 'to_dict') else None)

    def _answer_workload(self, query, coord, dep_graph, conflict,
                          priority, mission, escalation, workload) -> OrchestrationAnswer:
        if not workload:
            return OrchestrationAnswer(
                query_type=query.query_type,
                answer="Belum ada workload data.")
        w = workload
        answer = (f"**Workload** — status: {getattr(w, 'health_status', 'unknown')}\n"
                  f"- Pending approvals: {getattr(w, 'total_pending_approvals', 0)}\n"
                  f"- Pending missions: {getattr(w, 'total_pending_missions', 0)}\n"
                  f"- Total proposals: {getattr(w, 'total_proposals', 0)}\n"
                  f"- Critical approvals: {getattr(w, 'critical_approval_count', 0)}\n"
                  f"- Stalled proposals: {getattr(w, 'stalled_proposals', 0)}\n"
                  f"- Avg/approver: {getattr(w, 'avg_pending_per_approver', 0)}")
        return OrchestrationAnswer(
            query_type=query.query_type, answer=answer,
            data=workload.to_dict() if hasattr(workload, 'to_dict') else None)

    def _answer_escalation(self, query, coord, dep_graph, conflict,
                            priority, mission, escalation, workload) -> OrchestrationAnswer:
        if not escalation:
            return OrchestrationAnswer(
                query_type=query.query_type,
                answer="Belum ada escalation plan.")
        e = escalation
        answer = (f"**Escalation Plan** — {getattr(e, 'total', 0)} aktif\n"
                  f"- Reminders: {getattr(e, 'reminder_count', 0)}\n"
                  f"- Escalations: {getattr(e, 'escalation_count', 0)}\n"
                  f"- Critical: {getattr(e, 'critical_count', 0)}\n"
                  f"- Expired: {getattr(e, 'expired_count', 0)}")
        return OrchestrationAnswer(
            query_type=query.query_type, answer=answer,
            data=escalation.to_dict() if hasattr(escalation, 'to_dict') else None)
