"""Audit History — riwayat audit (Sprint 216).

In-memory, read-only. Tidak menulis disk.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple

from ..foundation.audit_descriptor import AuditDescriptor


@dataclass(frozen=True)
class AuditHistoryEntry:
    """Entri riwayat immutable."""
    audit_id: str
    action: str = "observed"
    category: str = "general"


@dataclass(frozen=True)
class AuditHistory:
    """Riwayat immutable."""
    entries: Tuple[AuditHistoryEntry, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))

    def size(self) -> int:
        return len(self.entries)


class AuditHistoryRecorder:
    """Perekam riwayat read-only (in-memory)."""

    def record(self, audits: List[AuditDescriptor]) -> AuditHistory:
        entries = tuple(
            AuditHistoryEntry(a.audit_id, category=a.category)
            for a in audits
        )
        return AuditHistory(entries=entries)
