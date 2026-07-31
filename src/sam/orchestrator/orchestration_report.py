# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 131 - Monitoring: orchestration_report.

Aggregate monitoring report. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass

from .orchestration_metrics import OrchestrationMetrics
from .orchestration_health import OrchestrationHealth
from .orchestration_statistics import OrchestrationStatistics


@dataclass(frozen=True)
class OrchestrationReport:
    """Immutable aggregate monitoring report."""

    metrics: OrchestrationMetrics
    health: OrchestrationHealth
    statistics: OrchestrationStatistics

    @property
    def ok(self) -> bool:
        return self.health.is_healthy and self.metrics.is_preview
