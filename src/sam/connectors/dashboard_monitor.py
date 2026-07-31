"""Dashboard Monitor — bridge read-only untuk UI monitoring.

Sprint 120 — Connector Monitoring.
5 ExecutionCard. Read-only.
"""
from __future__ import annotations
from typing import List

from .connector_registry import ConnectorRegistry
from .connector_statistics import ConnectorStatisticsCollector
from .dashboard_connector import ExecutionCard


class DashboardMonitorBridge:
    """Bridge dashboard monitoring — 5 ExecutionCard."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._stats = ConnectorStatisticsCollector(registry)

    def engine_card(self) -> ExecutionCard:
        s = self._stats.collect()
        return ExecutionCard(card_id="monitor.engine", title="Monitoring Engine",
                             summary=f"{s.healthy} healthy / {s.degraded} degraded",
                             detail="registry-backed", verdict="ok")

    def subsystem_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="monitor.subsystem", title="Monitor Subsystem",
                             summary="metrics & health", detail="preview-only",
                             verdict="ok")

    def summary_card(self) -> ExecutionCard:
        s = self._stats.collect()
        return ExecutionCard(card_id="monitor.summary", title="Monitor Summary",
                             summary=f"{s.total_connectors} connectors",
                             detail="all preview", verdict="ok")

    def detail_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="monitor.detail", title="Monitor Detail",
                             summary="snapshots & history available", detail="read-only",
                             verdict="ok")

    def verdict_card(self) -> ExecutionCard:
        return ExecutionCard(card_id="monitor.verdict", title="Monitor Verdict",
                             summary="Monitoring ready", detail="Ready for runtime",
                             verdict="ok")

    def cards(self) -> List[ExecutionCard]:
        return [self.engine_card(), self.subsystem_card(), self.summary_card(),
                self.detail_card(), self.verdict_card()]
