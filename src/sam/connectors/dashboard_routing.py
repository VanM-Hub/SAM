"""Dashboard Routing — bridge read-only untuk UI routing.

Sprint 117 — Connector Routing.
5 ExecutionCard. Read-only.
"""
from __future__ import annotations
from typing import List

from .connector_registry import ConnectorRegistry
from .connector_router import ConnectorRouter, RoutingPolicy
from .dashboard_connector import ExecutionCard


class DashboardRoutingBridge:
    """Bridge dashboard routing — 5 ExecutionCard."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._router = ConnectorRouter(registry)

    def engine_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="routing.engine", title="Routing Engine",
                             summary="capability-based routing", detail="deterministic",
                             verdict="ok")

    def subsystem_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="routing.subsystem", title="Routing Subsystem",
                             summary="route selection ready", detail="preview-only",
                             verdict="ok")

    def summary_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="routing.summary", title="Routing Summary",
                             summary=f"{self._registry.count()} connectors routable",
                             detail="by capability", verdict="ok")

    def detail_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="routing.detail", title="Routing Detail",
                             summary="policies & results", detail="read-only",
                             verdict="ok")

    def verdict_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="routing.verdict", title="Routing Verdict",
                             summary="Routes ready", detail="Ready for translation",
                             verdict="ok")

    def cards(self) -> List[ExecutionCard]:
        return [self.engine_card(), self.subsystem_card(), self.summary_card(),
                self.detail_card(), self.verdict_card()]
