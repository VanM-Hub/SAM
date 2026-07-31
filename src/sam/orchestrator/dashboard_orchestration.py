# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 123 - Orchestration Foundation: dashboard_orchestration.

Read-only dashboard bridge returning 5 ExecutionCards (reused card type).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .orchestration_registry import OrchestrationRegistry


class DashboardOrchestrationBridge:
    """Read-only bridge presenting orchestration state as cards."""

    def __init__(self, registry: OrchestrationRegistry) -> None:
        self._registry = registry

    def cards(self) -> Tuple[ExecutionCard, ...]:
        total = self._registry.count()
        names = ", ".join(d.name for d in self._registry.all()) or "-"
        return (
            ExecutionCard(
                card_id="orch-engine",
                title="Orchestration Engine",
                summary="Foundation registered",
                detail="Orchestration Runtime (Phase XII)",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="orch-runtimes",
                title="Registered Runtimes",
                summary="{0} runtime(s)".format(total),
                detail=names,
                verdict="ready",
            ),
            ExecutionCard(
                card_id="orch-founder",
                title="Foundation Sprint 123",
                summary="Context, request, descriptor, registry, builder",
                detail="Provider-agnostic, plan-only",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="orch-role",
                title="Role",
                summary="Arrange and direct - never execute",
                detail="No decision, approval, or execution",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="orch-pipeline",
                title="Pipeline Owner",
                summary="Connects all runtimes",
                detail="Guardian ... Connector -> Orchestration",
                verdict="ready",
            ),
        )

    def verdict_card(self) -> ExecutionCard:
        return ExecutionCard(
            card_id="orch-status",
            title="Orchestration Ready",
            summary="plan-only operational",
            detail="Orchestrates, does not execute",
            verdict="ready",
        )
