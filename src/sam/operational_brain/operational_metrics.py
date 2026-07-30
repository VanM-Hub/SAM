"""Operational Metrics — mengumpulkan metrik dari pipeline."

Menghitung throughput, cycle time, bottleneck detection.
Semua read-only, pure calculation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sam.operational_brain.operational_planning import OperationalPlanning
from sam.operational_brain.operational_scheduler import OperationalScheduler


@dataclass(frozen=True)
class OperationalMetrics:
    """Snapshot metrics — immutable."""
    total_candidates_generated: int = 0
    avg_plan_score: float = 0.0
    avg_priority_score: float = 0.0
    avg_schedule_position: float = 0.0
    blocked_items: int = 0
    schedule_conflicts: int = 0
    tier_distribution: Dict[str, int] = field(default_factory=dict)
    top_reasons: List[str] = field(default_factory=list)


class MetricsCollector:
    """Collects metrics from planning and scheduling."""

    def __init__(self):
        pass

    def collect(self, planning: OperationalPlanning,
                scheduler: OperationalScheduler) -> OperationalMetrics:
        plan = planning.last_plan
        sched = scheduler.schedule

        total_candidates = len(plan)
        avg_plan_score = self._avg([e.candidate.score for e in plan])
        avg_priority_score = self._avg([e.priority_score for e in plan])
        avg_sched_pos = self._avg([s.position for s in sched])

        blocked = sum(1 for s in sched if s.blocked_by)
        conflicting = sum(
            1 for s in sched
            for b in s.blocked_by
            if b not in {e.entry_id for e in plan}
        )

        tiers: Dict[str, int] = {}
        for e in plan:
            name = e.priority_tier.name
            tiers[name] = tiers.get(name, 0) + 1

        reasons = list({e.reason for e in plan})

        return OperationalMetrics(
            total_candidates_generated=total_candidates,
            avg_plan_score=round(avg_plan_score, 4),
            avg_priority_score=round(avg_priority_score, 4),
            avg_schedule_position=round(avg_sched_pos, 2),
            blocked_items=blocked,
            schedule_conflicts=conflicting,
            tier_distribution=tiers,
            top_reasons=reasons,
        )

    @staticmethod
    def _avg(vals: List[float]) -> float:
        return sum(vals) / len(vals) if vals else 0.0
