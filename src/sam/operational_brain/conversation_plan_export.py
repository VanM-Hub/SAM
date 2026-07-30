"""Conversation Plan Export Bridge — 6 query read-only."""

from typing import Any, Dict, List

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_plan_exporter import OperationalPlanExporter


class ConversationPlanExport:
    """Read-only conversation bridge untuk plan exporting."""

    def __init__(self, exporter: OperationalPlanExporter):
        self._exporter = exporter
        self._last_plan = None

    @property
    def query_count(self) -> int:
        return 6

    def query_plan_summary(self, ctx: OperationalContext) -> Dict[str, Any]:
        self._last_plan = self._exporter.run_full_pipeline(ctx)
        return self._exporter.summary(ctx)

    def query_plan_details(self, ctx: OperationalContext) -> Dict[str, Any]:
        plan = self._exporter.run_full_pipeline(ctx)
        doc = self._exporter.export_plan(plan)
        return {
            "title": doc.title,
            "entries": doc.entries,
            "schedule": doc.schedule,
            "metadata": doc.metadata,
        }

    def query_entries_only(self, ctx: OperationalContext) -> List[Dict[str, Any]]:
        plan = self._exporter.run_full_pipeline(ctx)
        doc = self._exporter.export_plan(plan)
        return doc.entries

    def query_schedule_only(self, ctx: OperationalContext) -> List[Dict[str, Any]]:
        plan = self._exporter.run_full_pipeline(ctx)
        doc = self._exporter.export_plan(plan)
        return doc.schedule

    def query_last_plan(self) -> Dict[str, Any]:
        if self._last_plan is None:
            return {"msg": "No plan generated yet"}
        return {
            "plan_id": self._last_plan.plan_id,
            "entries": self._last_plan.entries,
            "schedule_items": self._last_plan.schedule_items,
            "duration": self._last_plan.total_duration,
        }

    def query_quick_summary_by_source(self, source: str) -> Dict[str, Any]:
        ctx = OperationalContext(
            context_id=f"qs_{source}",
            timestamp=300.0,
            source=source,
            environment="normal",
        )
        return self._exporter.summary(ctx)
