"""Conversation Audit Bridge — 5 query read-only (Sprint 212)."""
from __future__ import annotations

from .audit_registry import AuditRegistry


class ConversationAuditBridge:
    """Bridge conversation — 5 query read-only fondasi audit."""

    def __init__(self, registry: AuditRegistry) -> None:
        self._registry = registry

    def query_1_count(self) -> dict:
        """Query 1 — jumlah audit."""
        return {"count": self._registry.count()}

    def query_2_exists(self, audit_id: str) -> dict:
        """Query 2 — cek ada/tidak inspeksi."""
        return {"exists": self._registry.exists(audit_id)}

    def query_3_empty(self) -> dict:
        """Query 3 — cek kosong."""
        return {"empty": self._registry.count() == 0}

    def query_4_categories(self) -> dict:
        """Query 4 — kategori audit."""
        cats = sorted({a.category for a in self._registry.all_entries()})
        return {"categories": cats}

    def query_5_immutable(self) -> dict:
        """Query 5 — sifat immutable dan no-execute."""
        return {"immutable": True, "no_execute": True}
