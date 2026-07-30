"""Operational Scheduler — mengatur urutan dan timeline pekerjaan.

Menerima plan entry terurut dari Planner + dependency info,
menghasilkan scheduled items dengan slot dan timeline.
Tidak memutuskan apa yang akan dieksekusi — hanya mengatur jadwal.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_planner import OperationalPlanner, PlanEntry, PlanSummary, PriorityTier
from sam.operational_brain.dependency_resolver import DependencyResolver, DependencyGraph, CycleError


@dataclass(frozen=True)
class ScheduledItem:
    """Satu item terjadwal — immutable."""
    schedule_id: str
    entry: PlanEntry
    position: int                              # 1-based dalam schedule
    estimated_start: Optional[float] = None    # simulated unix timestamp
    estimated_end: Optional[float] = None
    blocked_by: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Schedule:
    """Immutable schedule."""
    items: List[ScheduledItem] = field(default_factory=list)
    total_items: int = 0
    estimated_duration: float = 0.0
    conflicts: int = 0


class OperationalScheduler:
    """Mengatur urutan dan dependency dari plan entries."""

    def __init__(self, planner: Optional[OperationalPlanner] = None,
                 resolver: Optional[DependencyResolver] = None):
        self._planner = planner or OperationalPlanner()
        self._resolver = resolver or DependencyResolver()
        self._schedule: List[ScheduledItem] = []

    @property
    def schedule(self) -> List[ScheduledItem]:
        return list(self._schedule)

    @property
    def dependency_graph(self) -> DependencyGraph:
        return self._resolver.build_graph()

    def schedule_from_plan(self, entries: List[PlanEntry],
                           ctx: Optional[OperationalContext] = None) -> List[ScheduledItem]:
        """Generate schedule dari plan entries."""
        # Register goals from entries
        for e in entries:
            goal = e.candidate.goal
            try:
                self._resolver.add_goal(goal)
            except Exception:
                pass

        # Topological sort to handle dependencies
        deps = self._resolver.topological_sort() if not self._resolver.find_cycles() else []
        # Create a set of goal_ids present in entries
        entry_goal_ids = {e.candidate.goal.goal_id for e in entries}

        # Sort entries: by rank first, then topological priority
        def sort_key(e: PlanEntry) -> tuple:
            gid = e.candidate.goal.goal_id
            topo_pos = deps.index(gid) if gid in deps else 999
            return (topo_pos, e.rank)

        sorted_entries = sorted(entries, key=sort_key)

        # Build blocked_by for each entry based on dependencies
        blocked: Dict[str, List[str]] = {}
        for e in sorted_entries:
            gid = e.candidate.goal.goal_id
            blocked[e.entry_id] = []
            for dep_id in self._resolver.dependencies_of(gid):
                # find which entry carries this dep
                for other in sorted_entries:
                    if other.candidate.goal.goal_id == dep_id:
                        blocked[e.entry_id].append(other.entry_id)

        timestamp_base = ctx.timestamp if ctx else 100.0
        items: List[ScheduledItem] = []
        for pos, e in enumerate(sorted_entries, 1):
            t_start = timestamp_base + (pos - 1) * 10.0
            t_end = t_start + 5.0
            items.append(ScheduledItem(
                schedule_id=f"sch_{e.entry_id}",
                entry=e,
                position=pos,
                estimated_start=t_start,
                estimated_end=t_end,
                blocked_by=blocked.get(e.entry_id, []),
            ))

        self._schedule = items
        return list(items)

    def summary(self) -> Dict[str, Any]:
        if not self._schedule:
            return {"total_items": 0, "estimated_duration": 0.0, "conflicts": 0}
        total_items = len(self._schedule)
        conflicts = 0
        scheduled_ids = {e.entry.entry_id for e in self._schedule}
        for e in self._schedule:
            for b in e.blocked_by:
                if b not in scheduled_ids:
                    conflicts += 1
        start = self._schedule[0].estimated_start or 0.0
        end = self._schedule[-1].estimated_end or 0.0
        return {
            "total_items": total_items,
            "estimated_duration": round(end - start, 1),
            "conflicts": conflicts,
        }

    def schedule_dict(self) -> Dict[str, Any]:
        s = self.summary()
        items = []
        for item in self._schedule:
            items.append({
                "schedule_id": item.schedule_id,
                "entry_id": item.entry.entry_id,
                "position": item.position,
                "title": item.entry.candidate.goal.title,
                "tier": item.entry.priority_tier.name,
                "blocked_by": item.blocked_by,
            })
        s["items"] = items
        return s

    def clear(self) -> None:
        self._schedule.clear()
        self._resolver.clear()
