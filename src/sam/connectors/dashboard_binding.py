"""Dashboard Binding — bridge read-only untuk UI binding.

Sprint 115 — Connector Binding.
5 ExecutionCard. Read-only.
"""
from __future__ import annotations
from typing import List

from .binding_registry import BindingRegistry
from .dashboard_connector import ExecutionCard


class DashboardBindingBridge:
    """Bridge dashboard binding — 5 ExecutionCard."""

    def __init__(self, binding_registry: BindingRegistry) -> None:
        self._registry = binding_registry

    def engine_card(self) -> ExecutionCard:
        return ExecutionCard(
            card_id="binding.engine",
            title="Binding Engine",
            summary=f"{self._registry.count()} bindings",
            detail="preview-only",
            verdict="ok",
        )

    def subsystem_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="binding.subsystem", title="Binding Subsystem",
                             summary="Registry-backed", detail="read-only", verdict="ok")

    def summary_card(self) -> ExecutionCard:
        ids = [b.connector_id for b in self._registry.list_bindings()]
        return ExecutionCard(card_id="binding.summary", title="Binding Summary",
                             summary=", ".join(ids) if ids else "(none)",
                             detail="bound connectors", verdict="ok")

    def detail_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="binding.detail", title="Binding Detail",
                             summary="requests & results tracked", detail="in-memory",
                             verdict="ok")

    def verdict_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="binding.verdict", title="Binding Verdict",
                             summary="Bindings ready", detail="Ready for session",
                             verdict="ok")

    def cards(self) -> List[ExecutionCard]:
        return [self.engine_card(), self.subsystem_card(), self.summary_card(),
                self.detail_card(), self.verdict_card()]
