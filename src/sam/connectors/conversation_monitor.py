"""Conversation Monitor — bridge read-only untuk monitoring.

Sprint 120 — Connector Monitoring.
Query read-only ke health/statistics. Tidak ada mutasi.
"""
from __future__ import annotations
from typing import List

from .connector_registry import ConnectorRegistry
from .connector_health import ConnectorHealth, ConnectorHealthChecker
from .connector_statistics import ConnectorStatistics, ConnectorStatisticsCollector


class ConversationMonitorBridge:
    """Bridge conversation monitoring — read-only."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._health = ConnectorHealthChecker(registry)
        self._stats = ConnectorStatisticsCollector(registry)

    def health(self, connector_id: str) -> ConnectorHealth:
        return self._health.check(connector_id)

    def statistics(self) -> ConnectorStatistics:
        return self._stats.collect()

    def healthy_ids(self) -> List[str]:
        return [cid for cid in self._registry.list_ids()
                if self._health.check(cid).status == "healthy"]
