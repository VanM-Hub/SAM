"""Conversation Planning Bridge — 8 query read-only untuk planning."""

from typing import Any, Dict, List

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_planning import OperationalPlanning
from sam.operational_brain.operational_planner import PlanEntry, PriorityTier


class ConversationPlanning:
    """Read-only conversation bridge untuk planning subsystem."""

    def __init__(self, planning: OperationalPlanning):
        self._planning = planning

    @property
    def query_count(self) -> int:
        return 8

    def query_plan_summary(self) -> Dict[str, Any]:
        return self._planning.plan_dict()

    def query_last_plan(self) -> List[Dict[str, Any]]:
        return [
            {
                "entry_id": e.entry_id,
                "candidate_id": e.candidate.candidate_id,
                "rank": e.rank,
                "tier": e.priority_tier.name,
                "score": round(e.priority_score, 4),
                "title": e.candidate.goal.title,
                "goal_type": e.candidate.goal.goal_type.name,
            }
            for e in self._planning.last_plan
        ]

    def query_critical_entries(self) -> List[Dict[str, Any]]:
        return self._query_by_tier(PriorityTier.CRITICAL)

    def query_high_entries(self) -> List[Dict[str, Any]]:
        return self._query_by_tier(PriorityTier.HIGH)

    def query_top_n(self, n: int = 3) -> List[Dict[str, Any]]:
        return self.query_last_plan()[:n]

    def query_entry_by_id(self, entry_id: str) -> Dict[str, Any]:
        e = self._planning.find_entry(entry_id)
        if e is None:
            return {"error": f"Entry '{entry_id}' not found"}
        return {
            "entry_id": e.entry_id,
            "candidate_id": e.candidate.candidate_id,
            "rank": e.rank,
            "tier": e.priority_tier.name,
            "score": round(e.priority_score, 4),
            "title": e.candidate.goal.title,
            "goal_type": e.candidate.goal.goal_type.name,
            "reason": e.reason,
        }

    def query_plan_health(self) -> Dict[str, Any]:
        s = self._planning.summary()
        return {
            "total_entries": s.total_entries,
            "critical_pct": self._pct(s.critical, s.total_entries),
            "high_pct": self._pct(s.high, s.total_entries),
            "medium_pct": self._pct(s.medium, s.total_entries),
            "low_pct": self._pct(s.low, s.total_entries),
            "background_pct": self._pct(s.background, s.total_entries),
            "top_score": round(s.top_score, 4),
        }

    def query_planning_summary(self, ctx: OperationalContext) -> Dict[str, Any]:
        plan = self._planning.run(ctx)
        return {
            "context_id": ctx.context_id,
            "source": ctx.source,
            "entries": len(plan),
            "summary": self._planning.plan_dict(),
        }

    def _query_by_tier(self, tier: PriorityTier) -> List[Dict[str, Any]]:
        return [
            {
                "entry_id": e.entry_id,
                "candidate_id": e.candidate.candidate_id,
                "rank": e.rank,
                "score": round(e.priority_score, 4),
                "title": e.candidate.goal.title,
            }
            for e in self._planning.entries_by_tier(tier)
        ]

    @staticmethod
    def _pct(n: int, total: int) -> float:
        if total == 0:
            return 0.0
        return round(n / total * 100, 1)
