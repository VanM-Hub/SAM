"""Audit Builder — builder record audit (Sprint 214).

Builder HANYA membentuk DTO. TIDAK menyimpan, TIDAK menulis disk.
Build-only: tidak menyimpan ke registry, tidak mengeksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..model.audit_record import AuditRecord
from ..model.audit_entry import AuditEntry


@dataclass(frozen=True)
class AuditBuildResult:
    """Hasil build immutable."""
    record: AuditRecord = None
    ok: bool = False


class AuditBuilder:
    """Builder record audit — compose DTO saja, tanpa storage."""

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []

    def add_entry(self, entry: AuditEntry) -> "AuditBuilder":
        self._entries.append(entry)
        return self

    def build(self, record_id: str, action: str = "observe",
              source: str = "", target: str = "") -> AuditBuildResult:
        record = AuditRecord(
            record_id=record_id,
            action=action,
            source=source,
            target=target,
            entries=list(self._entries),
        )
        return AuditBuildResult(record=record, ok=True)
