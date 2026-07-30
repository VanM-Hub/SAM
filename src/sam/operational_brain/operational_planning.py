"""Operational Planning — orchestrator untuk planning pipeline.

Menggabungkan Planner + Prioritizer dan menyediakan antarmuka
ke conversation dan dashboard bridges.
"""

from typing import Dict, List, Optional

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_registry import OperationalRegistry
from sam.operational_brain.operational_builder import OperationalBuilder
from sam.operational_brain.operational_planner import (
    OperationalPlanner,
    OperationalPrioritizer,
    PlanEntry,
    PlanSummary,
    PriorityTier,
)


class OperationalPlanning:
    """Orchestrator untuk pipeline Context → Builder → Planner → Plan.

    BUKAN Decision Runtime — hanya planning, tidak memutuskan eksekusi.
    """

    def __init__(self, registry: Optional[OperationalRegistry] = None,
                 builder: Optional[OperationalBuilder] = None,
                 planner: Optional[OperationalPlanner] = None):
        self._registry = registry or OperationalRegistry()
        self._builder = builder or OperationalBuilder()
        self._prioritizer = OperationalPrioritizer()
        self._planner = planner or OperationalPlanner(self._prioritizer)
        self._last_context: Optional[OperationalContext] = None
        self._last_plan: List[PlanEntry] = []

    @property
    def last_plan(self) -> List[PlanEntry]:
        return list(self._last_plan)

    def run(self, ctx: OperationalContext) -> List[PlanEntry]:
        """Full pipeline: build candidates → prioritize → plan."""
        self._last_context = ctx
        candidates = self._builder.build(ctx)
        for c in candidates:
            self._registry.register_candidate(c)
        plan = self._planner.plan(candidates, ctx)
        self._last_plan = plan
        return list(plan)

    def summary(self) -> PlanSummary:
        return self._planner.summary()

    def plan_dict(self) -> Dict[str, object]:
        return self._planner.plan_dict()

    def find_entry(self, entry_id: str) -> Optional[PlanEntry]:
        for e in self._last_plan:
            if e.entry_id == entry_id:
                return e
        return None

    def entries_by_tier(self, tier: PriorityTier) -> List[PlanEntry]:
        return [e for e in self._last_plan if e.priority_tier == tier]
