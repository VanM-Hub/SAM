"""Conversation Catalog Bridge — query read-only (Sprint 184)."""
from __future__ import annotations

from .knowledge_catalog import KnowledgeCatalog
from .knowledge_version import KnowledgeVersionProvider


class ConversationCatalogBridge:
    """Bridge conversation — ringkasan katalog knowledge read-only."""

    def __init__(self, catalog: KnowledgeCatalog, version: KnowledgeVersionProvider = None) -> None:
        self._catalog = catalog
        self._version = version

    def summary(self) -> dict:
        return {"total": self._catalog.count()}

    def search(self, query: str) -> list:
        return [e.knowledge_id for e in self._catalog.search(query).entries]

    def version(self, knowledge_id: str) -> str:
        if self._version is None:
            return ""
        return self._version.version_of(knowledge_id)
