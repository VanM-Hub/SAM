"""Entry Builder — builder entri audit (Sprint 214)."""
from __future__ import annotations

from ..model.audit_entry import AuditEntry


class EntryBuilder:
    """Builder entri audit — membentuk DTO saja, tidak menyimpan."""

    def build(self, entry_id: str, kind: str = "info",
              message: str = "", actor: str = "",
              timestamp: int = 0) -> AuditEntry:
        return AuditEntry(
            entry_id=entry_id,
            kind=kind,
            message=message,
            actor=actor,
            timestamp=timestamp,
        )
