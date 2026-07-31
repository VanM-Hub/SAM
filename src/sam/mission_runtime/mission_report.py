# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 141 - Mission Monitoring: mission_report.

Aggregate monitoring report for a mission. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass

from .mission_metrics import MissionMetrics
from .mission_health import MissionHealth
from .mission_statistics import MissionStatistics


@dataclass(frozen=True)
class MissionReport:
    """Immutable aggregate monitoring report."""

    metrics: MissionMetrics
    health: MissionHealth
    statistics: MissionStatistics

    @property
    def ok(self) -> bool:
        return self.health.is_healthy and self.metrics.is_preview
