"""Memory Validator — validasi model memori (Sprint 173).

Phase XVII — Memory Runtime.
validate, validate_scope, validate_reference, validate_tags. Deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .memory_record import MemoryRecord
from .memory_reference import MemoryReference
from .memory_scope import MemoryScope
from .memory_tag import MemoryTag


@dataclass(frozen=True)
class MemoryValidation:
    """Hasil validasi memori (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class MemoryValidator:
    """Validator model memori. Deterministik."""

    def validate(self, record: MemoryRecord) -> MemoryValidation:
        issues = []
        if not record.record_id:
            issues.append("record_id required")
        if not record.memory_id:
            issues.append("memory_id required")
        return MemoryValidation(valid=not issues, issues=issues)

    def validate_scope(self, scope: MemoryScope) -> MemoryValidation:
        issues = []
        if not scope.scope_id:
            issues.append("scope_id required")
        return MemoryValidation(valid=not issues, issues=issues)

    def validate_reference(self, reference: MemoryReference) -> MemoryValidation:
        issues = []
        if not reference.reference_id:
            issues.append("reference_id required")
        if not reference.source_id:
            issues.append("source_id required")
        return MemoryValidation(valid=not issues, issues=issues)

    def validate_tags(self, tags: List[MemoryTag]) -> MemoryValidation:
        issues = []
        for tag in tags:
            if not tag.tag_id:
                issues.append("tag_id required")
        return MemoryValidation(valid=not issues, issues=issues)
