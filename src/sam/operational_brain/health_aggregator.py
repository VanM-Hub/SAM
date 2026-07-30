"""Operational Health Aggregator — aggregate readiness + metrics.

Menggabungkan readiness report dan metrics untuk penilaian kesehatan.
Read-only, pure function, tidak memutuskan eksekusi.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.readiness_checker import ReadinessChecker, ReadinessReport, ReadinessStatus
from sam.operational_brain.operational_planning import OperationalPlanning
from sam.operational_brain.operational_scheduler import OperationalScheduler
from sam.operational_brain.operational_metrics import MetricsCollector, OperationalMetrics


@dataclass(frozen=True)
class HealthReport:
    """Health report aggregated — immutable."""
    score: float
    status: str
    readiness: ReadinessReport
    metrics: OperationalMetrics
    summary: str = ""


class HealthAggregator:
    """Menggabungkan readiness + metrics menjadi health report."""

    def __init__(self, checker: ReadinessChecker = None, collector: MetricsCollector = None):
        self._checker = checker or ReadinessChecker()
        self._collector = collector or MetricsCollector()

    def assess(self, ctx: OperationalContext) -> HealthReport:
        readiness = self._checker.check_all(ctx)
        planning = OperationalPlanning()
        scheduler = OperationalScheduler()

        plan = planning.run(ctx)
        scheduler.schedule_from_plan(plan, ctx)
        metrics = self._collector.collect(planning, scheduler)

        overall_score = round(
            (readiness.overall_score * 0.6) + (metrics.avg_priority_score * 0.4),
            4,
        )

        status = "healthy"
        if overall_score < 0.3:
            status = "critical"
        elif overall_score < 0.6:
            status = "degraded"

        if readiness.overall_status in (ReadinessStatus.BLOCKED, ReadinessStatus.UNKNOWN):
            status = "blocked"

        summary = f"Score {overall_score}: Readiness {readiness.overall_status.name}, Metrics avg_priority={metrics.avg_priority_score}"

        return HealthReport(
            score=overall_score,
            status=status,
            readiness=readiness,
            metrics=metrics,
            summary=summary,
        )

    def report_dict(self, ctx: OperationalContext) -> Dict[str, Any]:
        report = self.assess(ctx)
        return {
            "health_score": round(report.score, 4),
            "health_status": report.status,
            "summary": report.summary,
            "readiness": {
                "score": round(report.readiness.overall_score, 4),
                "status": report.readiness.overall_status.name,
                "passed": report.readiness.passed,
                "total": report.readiness.total,
            },
            "metrics": {
                "total_candidates": report.metrics.total_candidates_generated,
                "avg_plan_score": report.metrics.avg_plan_score,
                "avg_priority_score": report.metrics.avg_priority_score,
                "blocked_items": report.metrics.blocked_items,
                "conflicts": report.metrics.schedule_conflicts,
                "tiers": report.metrics.tier_distribution,
            },
        }
