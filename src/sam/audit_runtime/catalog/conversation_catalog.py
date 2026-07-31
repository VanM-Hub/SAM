"""Conversation Catalog Bridge — 5 query read-only (Sprint 216)."""
from __future__ import annotations

from ..foundation.audit_descriptor import AuditDescriptor
from .audit_catalog import AuditCatalog
from .audit_index import AuditIndexer
from .audit_loader import AuditLoader
from .audit_version import AuditVersionProvider


class ConversationCatalogBridge:
    """Bridge conversation — 5 query read-only katalog audit."""

    def __init__(self, catalog: AuditCatalog) -> None:
        self._catalog = catalog

    def query_1_count(self) -> dict:
        """Query 1 — jumlah entri katalog."""
        return {"count": self._catalog.count()}

    def query_2_by_category(self, category: str) -> dict:
        """Query 2 — entri per kategori."""
        entries = self._catalog.by_category(category)
        return {"count": len(entries), "ids": [a.audit_id for a in entries]}

    def query_3_index(self) -> dict:
        """Query 3 — indeks ID."""
        idx = AuditIndexer().index(self._catalog.all_entries())
        return {"size": idx.size()}

    def query_4_loader(self) -> dict:
        """Query 4 — muat data in-memory (no file)."""
        res = AuditLoader().load(self._catalog.all_entries())
        return {"loaded": res.loaded, "count": res.count}

    def query_5_version(self) -> dict:
        """Query 5 — versi."""
        v = AuditVersionProvider().get()
        return {"runtime_version": v.runtime_version}
