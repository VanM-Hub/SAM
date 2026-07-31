"""Capability Matrix — DTO & engine matriks kapabilitas.

Sprint 114 — Connector Capability.
Matriks menghubungkan connector -> kapabilitas secara read-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .connector_registry import ConnectorRegistry


@dataclass(frozen=True)
class CapabilityMatrixEntry:
    """Entri matriks kapabilitas (connector-capability)."""
    connector_id: str
    capability_name: str
    support_level: str = "partial"  # none | partial | full
    operation_count: int = 0


@dataclass(frozen=True)
class CapabilityMatrix:
    """Matriks kapabilitas lengkap."""
    entries: List[CapabilityMatrixEntry] = field(default_factory=list)

    def by_connector(self, connector_id: str) -> List[CapabilityMatrixEntry]:
        return [e for e in self.entries if e.connector_id == connector_id]


class CapabilityMatrixBuilder:
    """Bangun matriks kapabilitas dari registry (read-only)."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def build(self) -> CapabilityMatrix:
        entries = []
        for cid in self._registry.list_ids():
            caps = self._registry.get_capabilities(cid)
            if not caps:
                entries.append(CapabilityMatrixEntry(cid, "none", "none", 0))
            for cap in caps:
                entries.append(CapabilityMatrixEntry(
                    cid, cap.name, "full", len(cap.supported_operations),
                ))
        return CapabilityMatrix(entries=entries)
