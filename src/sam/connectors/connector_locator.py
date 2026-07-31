"""Connector Locator — engine locator connector dari registry.

Sprint 113 — Connector Discovery.
Lokasi connector secara determinantik di dalam registry (tanpa network).
"""
from __future__ import annotations
from typing import List, Optional

from .connector_registry import ConnectorRegistry
from .connector_descriptor import ConnectorDescriptor
from .connector_discovery import DiscoveryResult, DiscoveryReport


class ConnectorLocator:
    """Lokasi connector berdasarkan registry secara read-only."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def locate(self, connector_id: str) -> Optional[ConnectorDescriptor]:
        """Lokasi connector by id."""
        return self._registry.get(connector_id)

    def locate_by_type(self, connector_type: str) -> List[ConnectorDescriptor]:
        """Lokasi semua connector dengan tipe tertentu."""
        out = []
        for cid in self._registry.list_ids():
            d = self._registry.get(cid)
            if d and d.connector_type == connector_type:
                out.append(d)
        return out

    def locate_by_tag(self, tag: str) -> List[ConnectorDescriptor]:
        """Lokasi connector yang memiliki tag tertentu."""
        out = []
        for cid in self._registry.list_ids():
            d = self._registry.get(cid)
            if d and tag in d.tags:
                out.append(d)
        return out

    def scan_all(self) -> DiscoveryReport:
        """Scan semua connector terdaftar."""
        ids = self._registry.list_ids()
        results = [
            DiscoveryResult(connector_id=cid, name=self._registry.get(cid).name,
                            connector_type=self._registry.get(cid).connector_type,
                            found=True)
            for cid in ids
        ]
        return DiscoveryReport(total_scanned=len(ids), found=len(results), results=results)
