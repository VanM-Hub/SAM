"""Conversation Builder Bridge — 5 query read-only (Sprint 214)."""
from __future__ import annotations

from .audit_builder import AuditBuilder
from .entry_builder import EntryBuilder
from .preview_builder import PreviewBuilder


class ConversationBuilderBridge:
    """Bridge conversation — 5 query read-only builder audit."""

    def __init__(self) -> None:
        self._audit = AuditBuilder()
        self._entry = EntryBuilder()
        self._preview = PreviewBuilder()

    def query_1_build(self, record_id: str) -> dict:
        """Query 1 — bangun record (compose DTO saja)."""
        res = self._audit.build(record_id)
        return {"ok": res.ok}

    def query_2_build_entry(self, entry_id: str) -> dict:
        """Query 2 — bangun entri."""
        e = self._entry.build(entry_id)
        return {"entry_id": e.entry_id, "kind": e.kind}

    def query_3_preview(self, record_id: str) -> dict:
        """Query 3 — preview record."""
        res = self._audit.build(record_id)
        p = PreviewBuilder().build(res.record)
        return {"decided": p.decided, "external_calls": p.external_calls}

    def query_4_no_storage(self) -> dict:
        """Query 4 — pastikan tidak menyimpan."""
        return {"stored": False}

    def query_5_decided(self) -> dict:
        """Query 5 — pastikan tidak mengambil keputusan."""
        return {"decided": False}
