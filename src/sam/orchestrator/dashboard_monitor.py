# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 131 - Monitoring: dashboard_monitor.

Read-only dashboard bridge for monitoring (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .orchestration_report import OrchestrationReport


class DashboardMonitorBridge:
    """Read-only bridge presenting monitoring as cards."""

    def cards_for(self, report: OrchestrationReport) -> Tuple[ExecutionCard, ...]:
        return (
            ExecutionCard(
                card_id="mon-health",
                title="Orchestration Health",
                summary=report.health.state,
                detail="State healthy/degraded/unknown",
                verdict="ok" if report.ok else "warn",
            ),
            ExecutionCard(
                card_id="mon-metrics",
                title="Metrics",
                summary="external_calls={0}".format(report.metrics.external_calls),
                detail="Preview-only (0 external)",
                verdict="ok",
            ),
            ExecutionCard(
                card_id="mon-stats",
                title="Statistics",
                summary="plans={0}".format(report.statistics.plans),
                detail="Runtimes={0}".format(report.statistics.runtimes),
                verdict="ok",
            ),
            ExecutionCard(
                card_id="mon-history",
                title="History",
                summary="Events recorded",
                detail="Sync, in-memory",
                verdict="ok",
            ),
            ExecutionCard(
                card_id="mon-sprint",
                title="Monitoring Sprint 131",
                summary="Metrics, health, history, statistics, report",
                detail="Monitoring",
                verdict="ok",
            ),
        )

    def verdict_card(self, report: OrchestrationReport) -> ExecutionCard:
        return ExecutionCard(
            card_id="mon-status",
            title="Orchestration Healthy",
            summary="preview-only operational",
            detail="Monitoring only - no execution",
            verdict="ok" if report.ok else "warn",
        )
