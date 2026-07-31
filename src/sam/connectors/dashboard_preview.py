"""Dashboard Preview — bridge read-only untuk UI preview.

Sprint 119 — Connector Preview.
5 ExecutionCard. Read-only.
"""
from __future__ import annotations
from typing import List

from .connector_registry import ConnectorRegistry
from .dashboard_connector import ExecutionCard


class DashboardPreviewBridge:
    """Bridge dashboard preview — 5 ExecutionCard."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def engine_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="preview.engine", title="Preview Engine",
                             summary="dry-run simulation only", detail="no external call",
                             verdict="ok")

    def subsystem_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="preview.subsystem", title="Preview Subsystem",
                             summary="preview-only guarantee", detail="network disabled",
                             verdict="ok")

    def summary_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="preview.summary", title="Preview Summary",
                             summary=f"{self._registry.count()} connectors previewable",
                             detail="dry-run", verdict="ok")

    def detail_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="preview.detail", title="Preview Detail",
                             summary="simulated effects", detail="0 external calls",
                             verdict="ok")

    def verdict_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="preview.verdict", title="Preview Verdict",
                             summary="Preview safe", detail="Ready for monitoring",
                             verdict="ok")

    def cards(self) -> List[ExecutionCard]:
        return [self.engine_card(), self.subsystem_card(), self.summary_card(),
                self.detail_card(), self.verdict_card()]
