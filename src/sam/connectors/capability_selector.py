"""Capability Selector — engine pemilih connector berdasarkan kapabilitas.

Sprint 114 — Connector Capability.
Pilih connector yang mendukung kapabilitas tertentu (read-only, deterministik).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .connector_registry import ConnectorRegistry


@dataclass(frozen=True)
class CapabilitySelection:
    """Hasil seleksi connector untuk sebuah kapabilitas."""
    capability_name: str
    selected_connectors: List[str] = field(default_factory=list)
    count: int = 0


class CapabilitySelector:
    """Selektor connector berdasarkan nama kapabilitas."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def select(self, capability_name: str) -> CapabilitySelection:
        matches = []
        for cid in self._registry.list_ids():
            for cap in self._registry.get_capabilities(cid):
                if cap.name == capability_name:
                    matches.append(cid)
                    break
        return CapabilitySelection(capability_name=capability_name,
                                   selected_connectors=matches, count=len(matches))
