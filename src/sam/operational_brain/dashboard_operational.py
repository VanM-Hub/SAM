"""Dashboard Bridge — 6 immutable cards."""

from dataclasses import dataclass
from typing import Any, Dict, List

from sam.operational_brain.operational_registry import OperationalRegistry
from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_builder import OperationalBuilder


@dataclass(frozen=True)
class OperationalDashboardCard:
    """Satu kartu dashboard — immutable."""
    title: str
    value: Any
    card_type: str = "info"
    metadata: Dict[str, Any] = None


class OperationalDashboard:
    """Dashboard 6 kartu immutable untuk Operational Brain."""

    def __init__(self, registry: OperationalRegistry = None):
        self._registry = registry or OperationalRegistry()
        self.card_count = 6

    def _overview_card(self, ctx: OperationalContext) -> OperationalDashboardCard:
        return OperationalDashboardCard(
            title="Operational Overview",
            value={
                "environment": ctx.environment,
                "source": ctx.source,
                "missions": len(ctx.active_missions),
                "resources": ctx.available_resources,
            },
            card_type="overview",
        )

    def _goals_card(self) -> OperationalDashboardCard:
        goals = self._registry.list_goals()
        return OperationalDashboardCard(
            title="Goals",
            value={
                "total": len(goals),
                "types": self._count_types(goals),
            },
            card_type="goals",
        )

    def _candidates_card(self) -> OperationalDashboardCard:
        s = self._registry.statistics()
        return OperationalDashboardCard(
            title="Candidates",
            value={
                "total": s.candidates,
                "avg_score": round(s.avg_score, 2),
                "avg_urgency": round(s.avg_urgency, 2),
            },
            card_type="candidates",
        )

    def _resources_card(self, ctx: OperationalContext) -> OperationalDashboardCard:
        return OperationalDashboardCard(
            title="Resources",
            value={
                "available": ctx.available_resources,
                "pending_decisions": ctx.pending_decisions,
                "pending_approvals": ctx.pending_approvals,
            },
            card_type="resources",
        )

    def _constraints_card(self, ctx: OperationalContext) -> OperationalDashboardCard:
        return OperationalDashboardCard(
            title="Constraints",
            value={
                "count": len(ctx.active_constraints),
                "items": list(ctx.active_constraints),
            },
            card_type="constraints",
        )

    def _registry_card(self) -> OperationalDashboardCard:
        s = self._registry.snapshot()
        return OperationalDashboardCard(
            title="Registry",
            value={
                "goals": s.goals,
                "candidates": s.candidates,
                "by_type": s.by_type,
            },
            card_type="registry",
        )

    def get_cards(self, ctx: OperationalContext) -> List[OperationalDashboardCard]:
        return [
            self._overview_card(ctx),
            self._goals_card(),
            self._candidates_card(),
            self._resources_card(ctx),
            self._constraints_card(ctx),
            self._registry_card(),
        ]

    @staticmethod
    def _count_types(goals) -> Dict[str, int]:
        types: Dict[str, int] = {}
        for g in goals:
            t = g.goal_type.name
            types[t] = types.get(t, 0) + 1
        return types
