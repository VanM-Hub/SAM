"""Connector Statistics — engine statistik connector.

Sprint 120 — Connector Monitoring.
Statistik agregat seluruh connector (read-only).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from .connector_registry import ConnectorRegistry


@dataclass(frozen=True)
class ConnectorStatistics:
    """Statistik agregat connector."""
    total_connectors: int = 0
    total_bindings: int = 0
    healthy: int = 0
    degraded: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)


class ConnectorStatisticsCollector:
    """Kumpulkan statistik connector."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def collect(self) -> ConnectorStatistics:
        by_type = {}
        healthy = degraded = 0
        from .connector_health import ConnectorHealthChecker
        checker = ConnectorHealthChecker(self._registry)
        for cid in self._registry.list_ids():
            h = checker.check(cid)
            d = self._registry.get(cid)
            if h.status == "healthy":
                healthy += 1
            elif d is not None:
                degraded += 1
            if d:
                by_type[d.connector_type] = by_type.get(d.connector_type, 0) + 1
        bindings = getattr(self._registry, "_bindings", {})
        return ConnectorStatistics(self._registry.count(), len(bindings),
                                   healthy, degraded, by_type)
