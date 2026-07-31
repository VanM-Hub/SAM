"""Dashboard Connector — bridge read-only untuk UI dashboard.

Sprint 112 — Connector Foundation.
5 ExecutionCard untuk UI. Read-only — tidak ada mutasi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .connector_registry import ConnectorRegistry
from .connector_descriptor import ConnectorDescriptor


@dataclass(frozen=True)
class ExecutionCard:
    """Kartu eksekusi dashboard (immutable)."""
    card_id: str
    title: str
    summary: str
    detail: str = ""
    verdict: str = "ok"


class DashboardConnectorBridge:
    """Bridge dashboard connector — 5 ExecutionCard."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def engine_card(self) -> ExecutionCard:
        return ExecutionCard(
            card_id="connector.engine",
            title="Connector Registry",
            summary=f"{self._registry.count()} connectors registered",
            detail="Preview-only registry",
            verdict="ok",
        )

    def subsystem_card(self) -> ExecutionCard:
        return ExecutionCard(
            card_id="connector.subsystem",
            title="Connector Subsystem",
            summary="Universal Connector Runtime",
            detail="Provider-agnostic, preview-only",
            verdict="ok",
        )

    def summary_card(self) -> ExecutionCard:
        s = self._registry.summary()
        return ExecutionCard(
            card_id="connector.summary",
            title="Connector Summary",
            summary=f"{s.total_connectors} total / {s.registered} registered",
            detail="by_type={}".format(s.by_type or {}),
            verdict="ok",
        )

    def detail_card(self) -> ExecutionCard:
        ids = self._registry.list_ids()
        return ExecutionCard(
            card_id="connector.detail",
            title="Connector Detail",
            summary=", ".join(ids) if ids else "(none)",
            detail="Registry contents",
            verdict="ok",
        )

    def verdict_card(self) -> ExecutionCard:
        return ExecutionCard(
            card_id="connector.verdict",
            title="Connector Verdict",
            summary="Foundation registered",
            detail="Preparing discovery",
            verdict="ok",
        )

    def cards(self) -> List[ExecutionCard]:
        return [
            self.engine_card(), self.subsystem_card(), self.summary_card(),
            self.detail_card(), self.verdict_card(),
        ]
