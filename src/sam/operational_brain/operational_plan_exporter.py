"""Operational Plan Exporter — mengekspor plan ke format terstruktur.

Plan mencakup goal, prioritas, jadwal, dependensi, dan ringkasan.
Menyediakan output dict, JSON-ready, dan format ringkas.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sam.operational_brain.operational_planning import OperationalPlanning
from sam.operational_brain.operational_scheduler import OperationalScheduler
from sam.operational_brain.operational_context import OperationalContext


@dataclass(frozen=True)
class OperationalPlan:
    """Plan operasional lengkap — immutable."""
    plan_id: str
    source: str
    entries: int = 0
    schedule_items: int = 0
    total_duration: float = 0.0
    plan_summary: Dict[str, Any] = field(default_factory=dict)
    schedule_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanDocument:
    """Dokumen plan — format siap-ekspor."""
    title: str
    entries: List[Dict[str, Any]] = field(default_factory=list)
    schedule: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class OperationalPlanExporter:
    """Mengekspor plan full pipeline (planning + scheduling).

    Membuat fresh instances per pipeline call agar tidak ada konflik registrasi.
    """

    def __init__(self):
        self._last_planning: Optional[OperationalPlanning] = None
        self._last_scheduler: Optional[OperationalScheduler] = None
        self._last_result: Optional[OperationalPlan] = None

    @property
    def last_result(self) -> Optional[OperationalPlan]:
        return self._last_result

    def run_full_pipeline(self, ctx: OperationalContext) -> OperationalPlan:
        """Full pipeline: context → plan → schedule → export."""
        planning = OperationalPlanning()
        scheduler = OperationalScheduler()
        plan_entries = planning.run(ctx)
        sched_items = scheduler.schedule_from_plan(plan_entries, ctx)
        plan_summary = planning.plan_dict()
        sched_summary = scheduler.summary()
        result = OperationalPlan(
            plan_id=f"plan_{ctx.context_id}",
            source=ctx.source,
            entries=len(plan_entries),
            schedule_items=len(sched_items),
            total_duration=round(sched_summary.get("estimated_duration", 0.0), 1),
            plan_summary=plan_summary,
            schedule_summary=sched_summary,
        )
        self._last_planning = planning
        self._last_scheduler = scheduler
        self._last_result = result
        return result

    def export_plan(self, plan: Optional[OperationalPlan] = None) -> PlanDocument:
        """Export plan ke dokument. Pakai self._last_* untuk data detail."""
        target = plan or self._last_result
        if target is None:
            return PlanDocument(title="No Plan Available")
        planning = self._last_planning or OperationalPlanning()
        scheduler = self._last_scheduler or OperationalScheduler()

        entries_list = []
        for e in planning.last_plan:
            entries_list.append({
                "entry_id": e.entry_id,
                "rank": e.rank,
                "tier": e.priority_tier.name,
                "score": round(e.priority_score, 4),
                "title": e.candidate.goal.title,
                "goal_type": e.candidate.goal.goal_type.name,
                "reason": e.reason,
            })

        sched_list = []
        for s in scheduler.schedule:
            sched_list.append({
                "schedule_id": s.schedule_id,
                "position": s.position,
                "entry_id": s.entry.entry_id,
                "title": s.entry.candidate.goal.title,
                "tier": s.entry.priority_tier.name,
                "blocked_by": s.blocked_by,
                "start": s.estimated_start,
                "end": s.estimated_end,
            })

        return PlanDocument(
            title=f"Operational Plan: {target.plan_id}",
            entries=entries_list,
            schedule=sched_list,
            metadata={
                "source": target.source,
                "total_entries": target.entries,
                "schedule_items": target.schedule_items,
                "duration": target.total_duration,
            },
        )

    def summary(self, ctx: OperationalContext) -> Dict[str, Any]:
        """Quick summary tanpa full pipeline."""
        plan = self.run_full_pipeline(ctx)
        return {
            "plan_id": plan.plan_id,
            "source": plan.source,
            "entries": plan.entries,
            "schedule_items": plan.schedule_items,
            "duration": plan.total_duration,
        }
