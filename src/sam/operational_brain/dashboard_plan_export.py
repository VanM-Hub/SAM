"""Dashboard Plan Export Bridge — 5 immutable cards untuk plan export."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_plan_exporter import OperationalPlanExporter


@dataclass(frozen=True)
class PlanExportCard:
    """Kartu dashboard plan export — immutable."""
    title: str
    value: Any
    card_type: str = "export"
    metadata: Dict[str, Any] = field(default_factory=dict)


class DashboardPlanExport:
    """Dashboard 5 kartu immutable untuk plan export."""

    def __init__(self, exporter: OperationalPlanExporter):
        self._exporter = exporter
        self.card_count = 5

    def _plan_card(self, ctx: OperationalContext) -> PlanExportCard:
        s = self._exporter.summary(ctx)
        return PlanExportCard(
            title="Plan",
            value=s,
            card_type="plan",
        )

    def _entries_card(self, ctx: OperationalContext) -> PlanExportCard:
        s = self._exporter.summary(ctx)
        return PlanExportCard(
            title="Plan Entries",
            value=s["entries"],
            card_type="entries",
        )

    def _schedule_card(self, ctx: OperationalContext) -> PlanExportCard:
        s = self._exporter.summary(ctx)
        return PlanExportCard(
            title="Schedule Items",
            value=s["schedule_items"],
            card_type="schedule",
        )

    def _duration_card(self, ctx: OperationalContext) -> PlanExportCard:
        s = self._exporter.summary(ctx)
        return PlanExportCard(
            title="Duration",
            value=s["duration"],
            card_type="duration",
        )

    def _source_card(self, ctx: OperationalContext) -> PlanExportCard:
        s = self._exporter.summary(ctx)
        return PlanExportCard(
            title="Source",
            value=s["source"],
            card_type="source",
        )

    def get_cards(self, ctx: OperationalContext) -> List[PlanExportCard]:
        return [
            self._plan_card(ctx),
            self._entries_card(ctx),
            self._schedule_card(ctx),
            self._duration_card(ctx),
            self._source_card(ctx),
        ]
