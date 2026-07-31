"""Conversation Model Bridge — query read-only (Sprint 173)."""
from __future__ import annotations

from .memory_record import MemoryRecord
from .memory_validator import MemoryValidator


class ConversationModelBridge:
    """Bridge conversation — ringkasan model memori read-only."""

    def __init__(self, record: MemoryRecord = None) -> None:
        self._record = record
        self._validator = MemoryValidator()

    def summary(self) -> dict:
        if self._record is None:
            return {"has_record": False}
        return {
            "has_record": True,
            "record_id": self._record.record_id,
            "scope": self._record.scope,
        }

    def validity(self) -> dict:
        if self._record is None:
            return {"valid": False, "issues": ["no record"]}
        v = self._validator.validate(self._record)
        return {"valid": v.valid, "issues": v.issues}
