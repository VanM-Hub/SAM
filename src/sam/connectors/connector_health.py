"""Connector Health — engine kesehatan connector.

Sprint 120 — Connector Monitoring.
Kesehatan connector berdasarkan konsistensi internal (deterministik).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .connector_registry import ConnectorRegistry


@dataclass(frozen=True)
class ConnectorHealth:
    """Kesehatan connector."""
    connector_id: str
    status: str = "unknown"  # healthy | degraded | unknown
    registered: bool = False
    issues: List[str] = field(default_factory=list)


class ConnectorHealthChecker:
    """Periksa kesehatan connector."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def check(self, connector_id: str) -> ConnectorHealth:
        d = self._registry.get(connector_id)
        if d is None:
            return ConnectorHealth(connector_id, "unknown", False, ["not registered"])
        caps = self._registry.get_capabilities(connector_id)
        issues = []
        if not caps:
            issues.append("no capabilities attached")
        status = "healthy" if not issues else "degraded"
        return ConnectorHealth(connector_id, status, True, issues)
