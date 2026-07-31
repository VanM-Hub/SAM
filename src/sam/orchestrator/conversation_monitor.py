# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 131 - Monitoring: conversation_monitor.

Read-only conversation bridge for monitoring.
"""
from __future__ import annotations

from typing import Dict

from .orchestration_metrics import OrchestrationMetrics
from .orchestration_health import OrchestrationHealth
from .orchestration_statistics import OrchestrationStatistics
from .orchestration_report import OrchestrationReport


class ConversationMonitorBridge:
    """Read-only bridge exposing orchestration monitoring."""

    def report(self) -> OrchestrationReport:
        return OrchestrationReport(
            metrics=OrchestrationMetrics(requests_counted=0, plans_built=0, external_calls=0),
            health=OrchestrationHealth(state="healthy", checks=("foundation",)),
            statistics=OrchestrationStatistics(plans=0, runtimes=0, preview_only=True),
        )

    def health(self) -> OrchestrationHealth:
        return self.report().health

    def summary(self) -> Dict[str, int]:
        return {"external_calls": 0, "preview": 1}
