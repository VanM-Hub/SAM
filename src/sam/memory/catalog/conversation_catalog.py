"""Conversation Catalog Bridge — query read-only (Sprint 176)."""
from __future__ import annotations

from .memory_catalog import MemoryCatalog
from .memory_version import MemoryVersionProvider


class ConversationCatalogBridge:
    """Bridge conversation — ringkasan katalog memori read-only."""

    def __init__(self, catalog: MemoryCatalog, version: MemoryVersionProvider = None) -> None:
        self._catalog = catalog
        self._version = version

    def summary(self) -> dict:
        return {"total": self._catalog.count()}

    def search(self, query: str) -> list:
        return [e.memory_id for e in self._catalog.search(query).entries]

    def version(self, memory_id: str) -> str:
        if self._version is None:
            return ""
        return self._version.version_of(memory_id)
