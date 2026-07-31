# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 132 - Runtime Engine: dashboard_engine.

Read-only dashboard bridge for the runtime engine (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .runtime_report import RuntimeReport


class DashboardEngineBridge:
    """Read-only bridge presenting engine status as cards."""

    def cards_for(self, report: RuntimeReport) -> Tuple[ExecutionCard, ...]:
        order = ", ".join(report.snapshot.pipeline.order) or "-"
        return (
            ExecutionCard(
                card_id="engine-status",
                title="Engine Status",
                summary=report.status.state,
                detail="Orchestration engine",
                verdict="ok" if report.ok else "warn",
            ),
            ExecutionCard(
                card_id="engine-ready",
                title="Engine Ready",
                summary=str(report.snapshot.ready),
                detail="Version {0}".format(report.snapshot.engine_version),
                verdict="ok",
            ),
            ExecutionCard(
                card_id="engine-pipeline",
                title="Engine Pipeline",
                summary="{0} stage(s)".format(report.snapshot.pipeline.stage_count),
                detail=order,
                verdict="ok",
            ),
            ExecutionCard(
                card_id="engine-coord",
                title="Unified Coordinator",
                summary="Entire pipeline orchestrated",
                detail="Guardian ... Connector -> Orchestration",
                verdict="ok",
            ),
            ExecutionCard(
                card_id="engine-sprint",
                title="Runtime Engine Sprint 132",
                summary="Engine, pipeline, status, report, snapshot",
                detail="Runtime Engine",
                verdict="ok",
            ),
        )

    def verdict_card(self, report: RuntimeReport) -> ExecutionCard:
        return ExecutionCard(
            card_id="engine-status-card",
            title="Orchestration Engine Ready",
            summary="plan-only operational",
            detail="Engine arranges and directs - never executes",
            verdict="ok" if report.ok else "warn",
        )
