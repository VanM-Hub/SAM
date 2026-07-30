"""Conversation Bridge — 10+ query operasional (read-only)."""

from typing import Any, Dict, List

from sam.operational_brain.operational_registry import OperationalRegistry
from sam.operational_brain.operational_builder import OperationalBuilder
from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_goal import OperationalGoal
from sam.operational_brain.operational_candidate import OperationalCandidate


class OperationalConversation:
    """Read-only conversation bridge untuk Operational Brain."""

    def __init__(self, registry: OperationalRegistry = None):
        self._registry = registry or OperationalRegistry()

    @property
    def query_count(self) -> int:
        return 10

    def query_context(self, ctx: OperationalContext) -> Dict[str, Any]:
        return ctx.to_dict()

    def query_goals(self) -> List[OperationalGoal]:
        return self._registry.list_goals()

    def query_candidates(self) -> List[OperationalCandidate]:
        return self._registry.list_candidates()

    def query_goal_summary(self) -> Dict[str, Any]:
        s = self._registry.statistics()
        return {
            "total_goals": s.goals,
            "by_type": s.by_type,
            "avg_priority": s.avg_priority,
        }

    def query_resource_summary(self, ctx: OperationalContext) -> Dict[str, Any]:
        return {
            "available_resources": ctx.available_resources,
            "environment": ctx.environment,
            "active_missions": len(ctx.active_missions),
            "pending_decisions": ctx.pending_decisions,
            "pending_approvals": ctx.pending_approvals,
        }

    def query_constraints(self, ctx: OperationalContext) -> List[str]:
        return list(ctx.active_constraints)

    def query_dependency_graph(self) -> Dict[str, List[str]]:
        deps: Dict[str, List[str]] = {}
        for g in self._registry.list_goals():
            deps[g.goal_id] = list(g.dependencies)
        return deps

    def query_statistics(self) -> Dict[str, Any]:
        s = self._registry.statistics()
        return {
            "goals": s.goals,
            "candidates": s.candidates,
            "by_type": s.by_type,
            "avg_priority": round(s.avg_priority, 2),
            "avg_score": round(s.avg_score, 2),
            "avg_urgency": round(s.avg_urgency, 2),
            "avg_confidence": round(s.avg_confidence, 2),
        }

    def query_snapshot(self) -> Dict[str, Any]:
        s = self._registry.snapshot()
        return {
            "goals": s.goals,
            "candidates": s.candidates,
            "by_type": s.by_type,
        }

    def query_builder_result(self, ctx: OperationalContext) -> List[Dict[str, Any]]:
        builder = OperationalBuilder()
        candidates = builder.build(ctx)
        return [
            {
                "candidate_id": c.candidate_id,
                "goal_type": c.goal.goal_type.name,
                "title": c.goal.title,
                "score": c.score,
                "urgency": c.urgency,
                "impact": c.impact,
                "effort": c.effort,
            }
            for c in candidates
        ]
