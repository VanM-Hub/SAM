"""Connector Catalog — engine katalog connector.

Sprint 113 — Connector Discovery.
Katalog memetakan connector terdaftar menjadi daftar terindeks (read-only).
"""
from __future__ import annotations
from typing import Dict, List, Optional

from .connector_registry import ConnectorRegistry
from .connector_descriptor import ConnectorDescriptor


class ConnectorCatalog:
    """Katalog connector terindeks dari registry."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry

    def _all(self) -> List[ConnectorDescriptor]:
        out = []
        for cid in self._registry.list_ids():
            d = self._registry.get(cid)
            if d is not None:
                out.append(d)
        return out

    def index(self) -> Dict[str, ConnectorDescriptor]:
        """Indeks penuh connector id -> descriptor."""
        return {d.connector_id: d for d in self._all()}

    def categories(self) -> List[str]:
        """Daftar kategori (connector_type) unik."""
        return sorted({d.connector_type for d in self._all()})

    def by_category(self, connector_type: str) -> List[ConnectorDescriptor]:
        """Ambil semua connector dalam satu kategori."""
        return [d for d in self._all() if d.connector_type == connector_type]
