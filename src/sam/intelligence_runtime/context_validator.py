"""Sprint 264 - Context Assembly: context_validator (validasi kelengkapan konteks)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .context_snapshot import ContextSnapshot


@dataclass(frozen=True)
class ContextIssue:
    """Isu konteks (section, kode, pesan)."""

    section: str
    code: str
    message: str


@dataclass(frozen=True)
class ContextValidator:
    """Memvalidasi snapshot konteks: semua section wajib hadir & non-kosong."""

    required: Tuple[str, ...]

    def validate(self, snapshot: ContextSnapshot) -> Tuple[ContextIssue, ...]:
        issues: List[ContextIssue] = []
        for name in self.required:
            if name not in snapshot.sections:
                issues.append(ContextIssue(
                    section=name, code="MISSING",
                    message=f"Section hilang: {name}"))
            elif not snapshot.sections[name]:
                issues.append(ContextIssue(
                    section=name, code="EMPTY",
                    message=f"Section kosong: {name}"))
        return tuple(issues)

    def is_complete(self, snapshot: ContextSnapshot) -> bool:
        return len(self.validate(snapshot)) == 0
