"""Conversation Discovery — bridge read-only untuk discovery connector.

Sprint 113 — Connector Discovery.
Query read-only ke locator/catalog/filter. Tidak ada mutasi.
"""
from __future__ import annotations
from typing import List

from .connector_registry import ConnectorRegistry
from .connector_locator import ConnectorLocator
from .connector_catalog import ConnectorCatalog
from .connector_discovery import DiscoveryReport


class ConversationDiscoveryBridge:
    """Bridge conversation discovery — query read-only."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._locator = ConnectorLocator(registry)
        self._catalog = ConnectorCatalog(registry)

    def scan(self) -> DiscoveryReport:
        """Scan semua connector terdaftar."""
        return self._locator.scan_all()

    def categories(self) -> List[str]:
        """Daftar kategori connector."""
        return self._catalog.categories()

    def by_type(self, connector_type: str) -> List[str]:
        """Daftar connector id dalam satu tipe."""
        return [d.connector_id for d in self._locator.locate_by_type(connector_type)]

    def total_discovered(self) -> int:
        """Jumlah connector yang ditemukan."""
        return self._registry.count()
