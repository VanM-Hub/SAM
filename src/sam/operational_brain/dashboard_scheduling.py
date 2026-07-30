"""Dashboard Scheduling Bridge — 5 immutable cards untuk scheduling."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sam.operational_brain.operational_scheduler import OperationalScheduler


@dataclass(frozen=True)
class SchedulingCard:
    """Satu kartu dashboard scheduling — immutable."""
    title: str
    value: Any
    card_type: str = "scheduling"
    metadata: Dict[str, Any] = field(default_factory=dict)


class DashboardScheduling:
    """Dashboard 5 kartu immutable untuk scheduling."""

    def __init__(self, scheduler: OperationalScheduler):
        self._scheduler = scheduler
        self.card_count = 5

    def _overview_card(self) -> SchedulingCard:
        s = self._scheduler.summary()
        return SchedulingCard(
            title="Schedule Overview",
            value={
                "total_items": s["total_items"],
                "duration": s["estimated_duration"],
                "conflicts": s["conflicts"],
            },
            card_type="overview",
        )

    def _tier_card(self) -> SchedulingCard:
        schedule = self._scheduler.schedule
        by_tier: Dict[str, int] = {}
        for item in schedule:
            t = item.entry.priority_tier.name
            by_tier[t] = by_tier.get(t, 0) + 1
        return SchedulingCard(
            title="By Tier",
            value=by_tier,
            card_type="tiers",
        )

    def _blocked_card(self) -> SchedulingCard:
        blocked_count = sum(1 for item in self._scheduler.schedule if item.blocked_by)
        return SchedulingCard(
            title="Blocked Items",
            value=blocked_count,
            card_type="blocked",
        )

    def _duration_card(self) -> SchedulingCard:
        s = self._scheduler.summary()
        return SchedulingCard(
            title="Duration",
            value=s["estimated_duration"],
            card_type="duration",
        )

    def _sequence_card(self) -> SchedulingCard:
        items = self._scheduler.schedule[:5]
        return SchedulingCard(
            title="Next 5 Items",
            value=[
                {"pos": i.position, "title": i.entry.candidate.goal.title,
                 "tier": i.entry.priority_tier.name}
                for i in items
            ],
            card_type="sequence",
        )

    def get_cards(self) -> List[SchedulingCard]:
        return [
            self._overview_card(),
            self._tier_card(),
            self._blocked_card(),
            self._duration_card(),
            self._sequence_card(),
        ]
