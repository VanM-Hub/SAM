# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 141 - Mission Monitoring: dashboard_monitor.

Read-only dashboard bridge for monitoring (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .mission_report import MissionReport


class DashboardMonitorBridge:
    """Read-only bridge presenting mission monitoring as cards."""

    def cards_for(self, report: MissionReport) -> Tuple[ExecutionCard, ...]:
        return (
            ExecutionCard(
                card_id="mon-health",
                title="Mission Health",
                summary=report.health.state,
                detail="healthy / degraded / critical",
                verdict="ok" if report.ok else "warn",
            ),
            ExecutionCard(
                card_id="mon-mission",
                title="Mission",
                summary=report.metrics.mission_id,
                detail="Monitored",
                verdict="ok",
            ),
            ExecutionCard(
                card_id="mon-progress",
                title="Progress",
                summary="{0:.0f}%".format(report.statistics.progress * 100),
                detail="{0}/{1} objectives".format(
                    report.metrics.checkpoints_reached, report.metrics.objectives_total
                ),
                verdict="ok",
            ),
            ExecutionCard(
                card_id="mon-preview",
                title="Preview-only",
                summary="external_calls=0",
                detail="No execution performed",
                verdict="ok",
            ),
            ExecutionCard(
                card_id="mon-sprint",
                title="Monitoring Sprint 141",
                summary="Metrics, health, history, statistics, report",
                detail="Mission Monitoring",
                verdict="ok",
            ),
        )

    def verdict_card(self, report: MissionReport) -> ExecutionCard:
        return ExecutionCard(
            card_id="mon-status",
            title="Mission Healthy",
            summary="preview-only operational",
            detail="Monitoring only - no execution",
            verdict="ok" if report.ok else "warn",
        )
