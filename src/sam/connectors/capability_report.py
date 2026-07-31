"""Capability Report — engine laporan kapabilitas.

Sprint 114 — Connector Capability.
Laporan ringkasan kapabilitas (read-only, immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .connector_registry import ConnectorRegistry
from .capability_matrix import CapabilityMatrixBuilder


@dataclass(frozen=True)
class CapabilityReport:
    """Laporan kapabilitas connector."""
    connector_id: str
    capability_names: List[str] = field(default_factory=list)
    total_capabilities: int = 0
    detail: str = ""


class CapabilityReporter:
    """Bangun laporan kapabilitas per connector."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._matrix = CapabilityMatrixBuilder(registry)

    def report(self, connector_id: str) -> CapabilityReport:
        caps = self._registry.get_capabilities(connector_id)
        names = [c.name for c in caps]
        return CapabilityReport(connector_id=connector_id,
                                capability_names=names,
                                total_capabilities=len(names),
                                detail=", ".join(names) if names else "(none)")
