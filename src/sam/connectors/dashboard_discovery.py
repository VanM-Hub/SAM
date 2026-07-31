"""Dashboard Discovery — bridge read-only untuk UI dashboard discovery.

Sprint 113 — Connector Discovery.
5 ExecutionCard. Read-only.
"""
from __future__ import annotations
from typing import List

from .connector_registry import ConnectorRegistry
from .connector_locator import ConnectorLocator
from .dashboard_connector import ExecutionCard


class DashboardDiscoveryBridge:
    """Bridge dashboard discovery — 5 ExecutionCard."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._locator = ConnectorLocator(registry)

    def engine_card(self) -> ExecutionCard:
        report = self._locator.scan_all()
        return ExecutionCard(
            card_id="discovery.engine",
            title="Discovery Engine",
            summary=f"{report.found} connectors discovered",
            detail=f"scanned {report.total_scanned}",
            verdict="ok",
        )

    def subsystem_card(self) -> ExecutionCard:
        return ExecutionCard(
            card_id="discovery.subsystem",
            title="Discovery Subsystem",
            summary="Registry-backed discovery",
            detail="No network calls",
            verdict="ok",
        )

    def summary_card(self) -> ExecutionCard:
        cats = self._locator.scan_all()
        return ExecutionCard(
            card_id="discovery.summary",
            title="Discovery Summary",
            summary=f"{len(cats.results)} found",
            detail="Preview-only",
            verdict="ok",
        )

    def detail_card(self) -> ExecutionCard:
        ids = self._registry.list_ids()
        return ExecutionCard(
            card_id="discovery.detail",
            title="Discovered Connectors",
            summary=", ".join(ids) if ids else "(none)",
            detail="Catalog contents",
            verdict="ok",
        )

    def verdict_card(self) -> ExecutionCard:
        return ExecutionCard(
            card_id="discovery.verdict",
            title="Discovery Verdict",
            summary="Discovery complete",
            detail="Ready for capability evaluation",
            verdict="ok",
        )

    def cards(self) -> List[ExecutionCard]:
        return [self.engine_card(), self.subsystem_card(), self.summary_card(),
                self.detail_card(), self.verdict_card()]
