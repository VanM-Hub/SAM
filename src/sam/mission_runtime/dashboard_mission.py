# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 134 - Mission Foundation: dashboard_mission.

Read-only dashboard bridge for mission foundation (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .mission_registry import MissionRegistry


class DashboardMissionBridge:
    """Read-only bridge presenting mission foundation as cards."""

    def __init__(self, registry: MissionRegistry) -> None:
        self._registry = registry

    def cards(self) -> Tuple[ExecutionCard, ...]:
        total = self._registry.count()
        names = ", ".join(m.name for m in self._registry.all()) or "-"
        return (
            ExecutionCard(
                card_id="mis-engine",
                title="Mission Engine",
                summary="Foundation registered",
                detail="Mission Runtime (Phase XIII)",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="mis-count",
                title="Open Missions",
                summary="{0} mission(s)".format(total),
                detail=names,
                verdict="ready",
            ),
            ExecutionCard(
                card_id="mis-founder",
                title="Foundation Sprint 134",
                summary="Context, descriptor, request, registry, builder",
                detail="Lifecycle management, plan-only",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="mis-role",
                title="Role",
                summary="Manage mission lifecycle",
                detail="No decision/approval/execution",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="mis-pipeline",
                title="Pipeline Owner",
                summary="Mission-oriented runtime",
                detail="Guardian ... Orchestration -> Mission",
                verdict="ready",
            ),
        )

    def verdict_card(self) -> ExecutionCard:
        return ExecutionCard(
            card_id="mis-status",
            title="Mission Runtime Ready",
            summary="lifecycle management operational",
            detail="Manages missions, does not execute",
            verdict="ready",
        )
