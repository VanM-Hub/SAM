"""Preview Builder — builder preview audit (Sprint 214).

Preview-only: menegakkan sifat preview dengan assertions.
External calls == 0, no storage, no execute.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..model.audit_record import AuditRecord


@dataclass(frozen=True)
class AuditPreviewDTO:
    """DTO preview immutable — menegakkan preview-only."""
    record: AuditRecord = None
    decided: bool = False
    external_calls: int = 0
    stored: bool = False

    def __post_init__(self) -> None:
        if self.decided:
            raise ValueError("audit preview cannot decide (decided=True forbidden)")
        if self.external_calls != 0:
            raise ValueError("audit preview must have external_calls == 0")
        if self.stored:
            raise ValueError("audit preview cannot store (stored=True forbidden)")


class PreviewBuilder:
    """Builder preview — compose DTO preview, tanpa storage/execution."""

    def __init__(self) -> None:
        self._notes: List[str] = []

    def add_note(self, note: str) -> "PreviewBuilder":
        self._notes.append(note)
        return self

    def build(self, record: AuditRecord) -> AuditPreviewDTO:
        return AuditPreviewDTO(record=record, decided=False,
                               external_calls=0, stored=False)
