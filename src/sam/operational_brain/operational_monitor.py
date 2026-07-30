"""Operational Monitor — monitoring loop state untuk operational brain.

Read-only, mengawasi perubahan pipeline state antar siklus.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_planning import OperationalPlanning
from sam.operational_brain.operational_scheduler import OperationalScheduler
from sam.operational_brain.health_aggregator import HealthAggregator


@dataclass(frozen=True)
class CycleSnapshot:
    """Snapshot satu siklus monitoring — immutable."""
    cycle_id: str
    context_diff: Dict[str, Any] = field(default_factory=dict)
    plan_entries: int = 0
    schedule_items: int = 0
    health_score: float = 0.0


class OperationalMonitor:
    """Memantau perubahan state pipeline antar siklus."""

    def __init__(self):
        self._cycles: List[CycleSnapshot] = []
        self._prev_context: Optional[OperationalContext] = None

    @property
    def cycles(self) -> List[CycleSnapshot]:
        return list(self._cycles)

    @property
    def cycle_count(self) -> int:
        return len(self._cycles)

    def run_cycle(self, ctx: OperationalContext) -> CycleSnapshot:
        planning = OperationalPlanning()
        scheduler = OperationalScheduler()
        planning.run(ctx)
        scheduler.schedule_from_plan(planning.last_plan, ctx)

        agg = HealthAggregator()
        health = agg.assess(ctx)

        context_diff: Dict[str, Any] = {}
        if self._prev_context:
            for attr in ["environment", "source", "active_missions", "pending_decisions",
                         "pending_approvals", "available_resources", "active_constraints"]:
                old = getattr(self._prev_context, attr)
                new = getattr(ctx, attr)
                if old != new:
                    context_diff[attr] = {"from": old, "to": new}

        snapshot = CycleSnapshot(
            cycle_id=f"cycle_{ctx.context_id}_{len(self._cycles)}",
            context_diff=context_diff,
            plan_entries=len(planning.last_plan),
            schedule_items=len(scheduler.schedule),
            health_score=round(health.score, 4),
        )
        self._cycles.append(snapshot)
        self._prev_context = ctx
        return snapshot

    def last_snapshot(self) -> Optional[CycleSnapshot]:
        if self._cycles:
            return self._cycles[-1]
        return None

    def clear(self) -> None:
        self._cycles.clear()
        self._prev_context = None
