"""Audit Index — indeks audit read-only (Sprint 216)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple

from ..foundation.audit_descriptor import AuditDescriptor


@dataclass(frozen=True)
class AuditIndex:
    """Indeks audit immutable — tuple ID tak bisa diubah."""
    record_ids: Tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "record_ids", tuple(self.record_ids))

    def contains(self, audit_id: str) -> bool:
        return audit_id in self.record_ids

    def size(self) -> int:
        return len(self.record_ids)


class AuditIndexer:
    """Indexer audit read-only."""

    def index(self, audits: List[AuditDescriptor]) -> AuditIndex:
        return AuditIndex(record_ids=tuple(a.audit_id for a in audits))
