"""Conversation Model Bridge — 5 query read-only (Sprint 213)."""
from __future__ import annotations

from .audit_validator import AuditValidator
from .audit_record import AuditRecord
from .audit_scope import VALID_SCOPES


class ConversationModelBridge:
    """Bridge conversation — 5 query read-only model audit."""

    def __init__(self) -> None:
        self._validator = AuditValidator()

    def query_1_scopes(self) -> dict:
        """Query 1 — daftar scope valid."""
        return {"valid_scopes": list(VALID_SCOPES)}

    def query_2_validate_scope(self, scope: str) -> dict:
        """Query 2 — validasi scope."""
        return {"ok": self._validator.validate_scope(scope)}

    def query_3_immutable(self) -> dict:
        """Query 3 — sifat immutable model."""
        return {"immutable": True}

    def query_4_actions(self) -> dict:
        """Query 4 — aksi audit yang didukung."""
        return {"actions": ["observe", "track", "verify"]}

    def query_5_validate(self, record_id: str) -> dict:
        """Query 5 — validasi record dasar."""
        r = AuditRecord(record_id)
        v = self._validator.validate(r)
        return {"valid": v.valid, "issues": v.issues}
