"""Health Checker — pengecekan kesehatan subsystem."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_health import HealthCheck, HealthReport


class HealthChecker:
    """Checker kesehatan — preview-only."""

    def __init__(self) -> None:
        self._checks: Dict[str, HealthCheck] = {}

    def check(self, check_id: str, subsystem: str, status: str = "healthy",
              latency_ms: float = 0.0, message: str = "") -> HealthCheck:
        hc = HealthCheck(
            check_id=check_id,
            subsystem=subsystem,
            status=status,
            latency_ms=latency_ms,
            message=message,
        )
        self._checks[check_id] = hc
        return hc

    def get(self, check_id: str) -> HealthCheck | None:
        return self._checks.get(check_id)

    def generate_report(self, report_id: str, timestamp: float) -> HealthReport:
        checks = list(self._checks.values())
        overall = "healthy"
        for c in checks:
            if c.status == "unhealthy":
                overall = "unhealthy"
                break
            if c.status == "degraded":
                overall = "degraded"
        return HealthReport(
            report_id=report_id,
            timestamp=timestamp,
            overall=overall,
            checks=checks,
        )

    def count_checks(self) -> int:
        return len(self._checks)

    def list_unhealthy(self) -> List[HealthCheck]:
        return [c for c in self._checks.values()
                if c.status in ("unhealthy", "degraded")]
