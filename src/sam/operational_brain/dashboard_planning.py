"""Dashboard Planning Bridge — 5 immutable cards untuk planning."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_planning import OperationalPlanning


@dataclass(frozen=True)
class PlanningCard:
    """Satu kartu dashboard untuk planning — immutable."""
    title: str
    value: Any
    card_type: str = "planning"
    metadata: Dict[str, Any] = field(default_factory=dict)


class DashboardPlanning:
    """Dashboard 5 kartu immutable untuk planning."""

    def __init__(self, planning: OperationalPlanning):
        self._planning = planning
        self.card_count = 5

    def _summary_card(self) -> PlanningCard:
        s = self._planning.summary()
        return PlanningCard(
            title="Plan Summary",
            value={
                "total": s.total_entries,
                "critical": s.critical,
                "high": s.high,
                "medium": s.medium,
                "low": s.low,
                "background": s.background,
            },
            card_type="summary",
        )

    def _top_entry_card(self) -> PlanningCard:
        plan = self._planning.last_plan
        if not plan:
            return PlanningCard(title="Top Entry", value={"msg": "No plan"}, card_type="top")
        e = plan[0]
        return PlanningCard(
            title="Top Priority",
            value={
                "entry_id": e.entry_id,
                "title": e.candidate.goal.title,
                "tier": e.priority_tier.name,
                "score": round(e.priority_score, 4),
            },
            card_type="top",
        )

    def _critical_count_card(self) -> PlanningCard:
        s = self._planning.summary()
        return PlanningCard(
            title="Critical Items",
            value=s.critical,
            card_type="critical",
        )

    def _score_range_card(self) -> PlanningCard:
        s = self._planning.summary()
        return PlanningCard(
            title="Score Range",
            value={
                "top": round(s.top_score, 4),
                "bottom": round(s.bottom_score, 4),
            },
            card_type="range",
        )

    def _tier_distribution_card(self) -> PlanningCard:
        s = self._planning.summary()
        return PlanningCard(
            title="Tier Distribution",
            value={
                "CRITICAL": s.critical,
                "HIGH": s.high,
                "MEDIUM": s.medium,
                "LOW": s.low,
                "BACKGROUND": s.background,
            },
            card_type="distribution",
        )

    def get_cards(self, ctx: OperationalContext) -> List[PlanningCard]:
        """Generate 5 planning cards."""
        return [
            self._summary_card(),
            self._top_entry_card(),
            self._critical_count_card(),
            self._score_range_card(),
            self._tier_distribution_card(),
        ]
