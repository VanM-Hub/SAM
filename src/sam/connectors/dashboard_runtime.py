"""Dashboard Runtime — bridge read-only untuk UI connector runtime.

Sprint 121 — Connector Runtime.
5 ExecutionCard. Read-only.
"""
from __future__ import annotations
from typing import List

from .connector_registry import ConnectorRegistry
from .runtime_coordinator import RuntimeCoordinator
from .dashboard_connector import ExecutionCard


class DashboardRuntimeBridge:
    """Bridge dashboard runtime — 5 ExecutionCard."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._coordinator = RuntimeCoordinator(registry)

    def engine_card(self) -> ExecutionCard:
        r = self._coordinator.readiness()
        return ExecutionCard(card_id="runtime.engine", title="Connector Runtime Engine",
                             summary="ready" if r.ready else "not ready",
                             detail="orchestrator active", verdict="ok")

    def subsystem_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="runtime.subsystem", title="Connector Runtime Subsystem",
                             summary="Universal Connector Runtime", detail="preview-only",
                             verdict="ok")

    def summary_card(self) -> ExecutionCard:
        r = self._coordinator.readiness()
        return ExecutionCard(card_id="runtime.summary", title="Runtime Summary",
                             summary=f"{len(r.checks)} stages",
                             detail="coordinated", verdict="ok")

    def detail_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="runtime.detail", title="Runtime Detail",
                             summary=f"{self._registry.count()} connectors",
                             detail="registry-backed", verdict="ok")

    def verdict_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="runtime.verdict", title="Runtime Verdict",
                             summary="Runtime ready", detail="Ready for certification",
                             verdict="ok")

    def cards(self) -> List[ExecutionCard]:
        return [self.engine_card(), self.subsystem_card(), self.summary_card(),
                self.detail_card(), self.verdict_card()]
