# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 142 - Mission Runtime: dashboard_runtime.

Read-only dashboard bridge for the mission runtime (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .mission_reporter import MissionReporter


class DashboardRuntimeBridge:
    """Read-only bridge presenting mission runtime as cards."""

    def cards_for(self, report: MissionReporter) -> Tuple[ExecutionCard, ...]:
        stages = ", ".join(report.snapshot.pipeline.stages)
        return (
            ExecutionCard(
                card_id="mrt-status",
                title="Mission Runtime Status",
                summary=report.status.state,
                detail="Mission Runtime",
                verdict="ok" if report.ok else "warn",
            ),
            ExecutionCard(
                card_id="mrt-version",
                title="Runtime Version",
                summary=report.snapshot.runtime_version,
                detail="Mission lifecycle manager",
                verdict="ok",
            ),
            ExecutionCard(
                card_id="mrt-enterprise",
                title="Mission-Oriented",
                summary="Single shared object",
                detail="All runtimes work toward one Mission",
                verdict="ok",
            ),
            ExecutionCard(
                card_id="mrt-pipeline",
                title="Capture Pipeline",
                summary="{0} stage(s)".format(report.snapshot.pipeline.stage_count),
                detail=stages,
                verdict="ok",
            ),
            ExecutionCard(
                card_id="mrt-sprint",
                title="Mission Runtime Sprint 142",
                summary="Runtime, pipeline, snapshot, status, reporter",
                detail="Mission Runtime",
                verdict="ok",
            ),
        )

    def verdict_card(self, report: MissionReporter) -> ExecutionCard:
        return ExecutionCard(
            card_id="mrt-card",
            title="Mission Runtime Ready",
            summary="lifecycle management operational",
            detail="Manages missions - never executes",
            verdict="ok" if report.ok else "warn",
        )
