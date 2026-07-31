"""Conversation Model Bridge — query read-only (Sprint 181)."""
from __future__ import annotations

from .knowledge_record import KnowledgeRecord
from .knowledge_validator import KnowledgeValidator


class ConversationModelBridge:
    """Bridge conversation — ringkasan model knowledge read-only."""

    def __init__(self, record: KnowledgeRecord = None) -> None:
        self._record = record
        self._validator = KnowledgeValidator()

    def summary(self) -> dict:
        if self._record is None:
            return {"has_record": False}
        return {
            "has_record": True,
            "record_id": self._record.record_id,
            "facts": len(self._record.facts),
            "relations": len(self._record.relations),
        }

    def validity(self) -> dict:
        if self._record is None:
            return {"valid": False, "issues": ["no record"]}
        v = self._validator.validate(self._record)
        return {"valid": v.valid, "issues": v.issues}
