# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 127 - Dependency Resolver: dashboard_dependency.

Read-only dashboard bridge for dependency resolution (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .dependency_report import DependencyReport


class DashboardDependencyBridge:
    """Read-only bridge presenting dependency state as cards."""

    def cards_for(self, report: DependencyReport) -> Tuple[ExecutionCard, ...]:
        order = ", ".join(report.order) or "-"
        return (
            ExecutionCard(
                card_id="dep-order",
                title="Dependency Order",
                summary="{0} runtime(s)".format(len(report.order)),
                detail=order,
                verdict="ready",
            ),
            ExecutionCard(
                card_id="dep-acyclic",
                title="Acyclic",
                summary="No dependency cycles",
                detail="{0} edge(s)".format(report.edge_count),
                verdict="ready",
            ),
            ExecutionCard(
                card_id="dep-resolver",
                title="Resolved",
                summary="Topological order produced",
                detail="Dependencies first",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="dep-snapshot",
                title="Snapshot Available",
                summary="Graph state captured",
                detail="No execution performed",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="dep-sprint",
                title="Dependency Sprint 127",
                summary="Graph, resolver, validator, report, snapshot",
                detail="Dependency Resolver",
                verdict="ready",
            ),
        )

    def verdict_card(self, report: DependencyReport) -> ExecutionCard:
        return ExecutionCard(
            card_id="dep-status",
            title="Dependency Resolved",
            summary="order of {0} runtime(s)".format(len(report.order)),
            detail="Ordering only - no execution",
            verdict="ready",
        )
