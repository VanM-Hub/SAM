"""Conversation Scheduling Bridge — 7 query read-only untuk scheduling."""

from typing import Any, Dict, List

from sam.operational_brain.operational_scheduler import OperationalScheduler


class ConversationScheduling:
    """Read-only conversation bridge untuk scheduling subsystem."""

    def __init__(self, scheduler: OperationalScheduler):
        self._scheduler = scheduler

    @property
    def query_count(self) -> int:
        return 7

    def query_schedule_summary(self) -> Dict[str, Any]:
        return self._scheduler.summary()

    def query_full_schedule(self) -> List[Dict[str, Any]]:
        s = self._scheduler.schedule_dict()
        return s.get("items", [])

    def query_schedule_by_tier(self, tier_name: str) -> List[Dict[str, Any]]:
        results = []
        for item in self._scheduler.schedule:
            if item.entry.priority_tier.name == tier_name:
                results.append(self._item_to_dict(item))
        return results

    def query_blocked_items(self) -> List[Dict[str, Any]]:
        return [
            self._item_to_dict(item)
            for item in self._scheduler.schedule
            if item.blocked_by
        ]

    def query_dependency_graph(self) -> Dict[str, Any]:
        dg = self._scheduler.dependency_graph
        return {
            "nodes": list(dg.nodes),
            "topological_order": list(dg.topological_order),
            "has_cycles": dg.has_cycles,
        }

    def query_topology(self) -> List[str]:
        dg = self._scheduler.dependency_graph
        return list(dg.topological_order)

    def query_schedule_conflicts(self) -> Dict[str, Any]:
        all_items = self._scheduler.schedule
        blocked_ids = {b for item in all_items for b in item.blocked_by}
        existing_ids = {item.entry.entry_id for item in all_items}
        unresolved = list(blocked_ids - existing_ids)
        return {"unresolved_dependencies": unresolved, "conflict_count": len(unresolved)}

    @staticmethod
    def _item_to_dict(item) -> Dict[str, Any]:
        return {
            "schedule_id": item.schedule_id,
            "entry_id": item.entry.entry_id,
            "position": item.position,
            "title": item.entry.candidate.goal.title,
            "tier": item.entry.priority_tier.name,
            "blocked_by": item.blocked_by,
        }
