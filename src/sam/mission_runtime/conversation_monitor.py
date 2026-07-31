# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 141 - Mission Monitoring: conversation_monitor.

Read-only conversation bridge for mission monitoring.
"""
from __future__ import annotations

from typing import Dict

from .mission_metrics import MissionMetrics
from .mission_health import MissionHealth
from .mission_statistics import MissionStatistics
from .mission_report import MissionReport


class ConversationMonitorBridge:
    """Read-only bridge exposing mission monitoring."""

    def report(self, mission_id: str) -> MissionReport:
        return MissionReport(
            metrics=MissionMetrics(
                mission_id=mission_id, objectives_total=0, checkpoints_reached=0, external_calls=0
            ),
            health=MissionHealth(mission_id=mission_id, state="healthy"),
            statistics=MissionStatistics(mission_id=mission_id, progress=0.0, preview_only=True),
        )

    def health(self, mission_id: str) -> MissionHealth:
        return self.report(mission_id).health

    def summary(self) -> Dict[str, int]:
        return {"external_calls": 0, "preview": 1}
