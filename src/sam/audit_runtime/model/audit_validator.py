"""Audit Validator — validasi audit deterministik (Sprint 213).

Read-only: memvalidasi model audit. Tidak menyimpan, tidak eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .audit_record import AuditRecord


@dataclass(frozen=True)
class AuditValidation:
    """Hasil validasi immutable."""
    valid: bool = False
    issues: List[str] = field(default_factory=list)


class AuditValidator:
    """Validator audit read-only dan deterministik."""

    def validate(self, record: AuditRecord) -> AuditValidation:
        issues = []
        if not record.record_id.strip():
            issues.append("empty record_id")
        if record.action not in ("observe", "track", "verify"):
            issues.append(f"unsupported action: {record.action}")
        if record.immutable is not True:
            issues.append("record must be immutable")
        return AuditValidation(valid=len(issues) == 0, issues=issues)

    def validate_scope(self, scope: str) -> bool:
        from .audit_scope import VALID_SCOPES
        return scope in VALID_SCOPES

    def validate_entries(self, record: AuditRecord) -> bool:
        return all(e.entry_id for e in record.entries)
