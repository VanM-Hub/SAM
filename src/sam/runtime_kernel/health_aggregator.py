"""Health Aggregator — agregator kesehatan."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_health import HealthCheck, HealthReport


class HealthAggregator:
    """Agregator kesehatan — preview-only."""

    def aggregate(self, reports: List[HealthReport]) -> str:
        if not reports:
            return "unknown"
        for r in reports:
            if r.overall == "unhealthy":
                return "unhealthy"
        for r in reports:
            if r.overall == "degraded":
                return "degraded"
        return "healthy"

    def count_reports(self, reports: List[HealthReport]) -> int:
        return len(reports)

    def merge_checks(self, reports: List[HealthReport]) -> List[HealthCheck]:
        checks: List[HealthCheck] = []
        for r in reports:
            checks.extend(r.checks)
        return checks
