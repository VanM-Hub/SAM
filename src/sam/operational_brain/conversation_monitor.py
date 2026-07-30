"""Conversation Monitor Bridge — 5 query read-only untuk monitoring."""

from typing import Any, Dict, List

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_monitor import OperationalMonitor


class ConversationMonitor:
    """Conversation bridge untuk monitoring."""

    def __init__(self, monitor: OperationalMonitor):
        self._monitor = monitor

    @property
    def query_count(self) -> int:
        return 5

    def query_cycle_count(self) -> int:
        return self._monitor.cycle_count

    def query_last_snapshot(self) -> Dict[str, Any]:
        snap = self._monitor.last_snapshot()
        if snap is None:
            return {"msg": "No cycles yet"}
        return {
            "cycle_id": snap.cycle_id,
            "context_diff": snap.context_diff,
            "plan_entries": snap.plan_entries,
            "schedule_items": snap.schedule_items,
            "health_score": snap.health_score,
        }

    def query_cycle_history(self) -> List[Dict[str, Any]]:
        return [
            {
                "cycle_id": c.cycle_id,
                "plan_entries": c.plan_entries,
                "schedule_items": c.schedule_items,
                "health_score": c.health_score,
            }
            for c in self._monitor.cycles
        ]

    def query_recent_changes(self) -> List[Dict[str, Any]]:
        snap = self._monitor.last_snapshot()
        if snap is None:
            return []
        return [
            {"attribute": k, "from": v["from"], "to": v["to"]}
            for k, v in snap.context_diff.items()
        ]

    def query_run_cycle(self, ctx: OperationalContext) -> Dict[str, Any]:
        snap = self._monitor.run_cycle(ctx)
        return {
            "cycle_id": snap.cycle_id,
            "plan_entries": snap.plan_entries,
            "schedule_items": snap.schedule_items,
            "health_score": snap.health_score,
        }
