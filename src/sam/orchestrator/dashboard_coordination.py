# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 129 - Coordination: dashboard_coordination.

Read-only dashboard bridge for coordination (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .coordination_report import CoordinationReport


class DashboardCoordinationBridge:
    """Read-only bridge presenting coordination as cards."""

    def cards_for(self, report: CoordinationReport) -> Tuple[ExecutionCard, ...]:
        runtimes = ", ".join(s.runtime_id for s in report.states) or "-"
        return (
            ExecutionCard(
                card_id="coord-runtimes",
                title="Coordinated Runtimes",
                summary="{0} runtime(s)".format(len(report.states)),
                detail=runtimes,
                verdict="ready",
            ),
            ExecutionCard(
                card_id="coord-all",
                title="All Coordinated",
                summary=str(report.all_coordinated),
                detail="Harmonized chain",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="coord-states",
                title="Coordination States",
                summary="{0} coordinated".format(report.coordinated_count),
                detail="Planned -> ready -> coordinated",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="coord-history",
                title="History Tracked",
                summary="Coordination events recorded",
                detail="No execution performed",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="coord-sprint",
                title="Coordination Sprint 129",
                summary="Coordinator, state, report, validator, history",
                detail="Coordination",
                verdict="ready",
            ),
        )

    def verdict_card(self, report: CoordinationReport) -> ExecutionCard:
        return ExecutionCard(
            card_id="coord-status",
            title="Coordinated",
            summary="{0} runtime(s) harmonized".format(len(report.states)),
            detail="Coordination only - no execution",
            verdict="ready",
        )
