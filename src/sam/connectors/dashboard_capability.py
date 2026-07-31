"""Dashboard Capability — bridge read-only untuk UI kapabilitas.

Sprint 114 — Connector Capability.
5 ExecutionCard. Read-only.
"""
from __future__ import annotations
from typing import List

from .connector_registry import ConnectorRegistry
from .dashboard_connector import ExecutionCard


class DashboardCapabilityBridge:
    """Bridge dashboard capability — 5 ExecutionCard."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def engine_card(self) -> ExecutionCard:
        return ExecutionCard(
            card_id="capability.engine",
            title="Capability Engine",
            summary="Capability evaluation ready",
            detail="Provider-agnostic",
            verdict="ok",
        )

    def subsystem_card(self) -> ExecutionCard:
        return ExecutionCard(
            card_id="capability.subsystem",
            title="Capability Subsystem",
            summary="Profile & matrix",
            detail="Preview-only",
            verdict="ok",
        )

    def summary_card(self) -> ExecutionCard:
        return ExecutionCard(
            card_id="capability.summary",
            title="Capability Summary",
            summary=f"{self._registry.count()} connectors profiled",
            detail="by capability",
            verdict="ok",
        )

    def detail_card(self) -> ExecutionCard:
        return ExecutionCard(
            card_id="capability.detail",
            title="Capabilities",
            summary="profiles, matrix, reports available",
            detail="read-only",
            verdict="ok",
        )

    def verdict_card(self) -> ExecutionCard:
        return ExecutionCard(
            card_id="capability.verdict",
            title="Capability Verdict",
            summary="Profiles evaluated",
            detail="Ready for binding",
            verdict="ok",
        )

    def cards(self) -> List[ExecutionCard]:
        return [self.engine_card(), self.subsystem_card(), self.summary_card(),
                self.detail_card(), self.verdict_card()]
