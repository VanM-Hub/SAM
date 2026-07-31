"""Audit Loader — loader audit (Sprint 216).

Loader TANPA membaca file/disk. Hanya menerima data in-memory dan
membentuk DTO. No file IO, no cache.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.audit_descriptor import AuditDescriptor


@dataclass(frozen=True)
class AuditLoadResult:
    """Hasil muat immutable."""
    audits: List[AuditDescriptor] = field(default_factory=list)
    count: int = 0
    loaded: bool = False


class AuditLoader:
    """Loader audit — no file read, no cache."""

    def load(self, data: List[AuditDescriptor]) -> AuditLoadResult:
        result = AuditLoadResult(
            audits=list(data),
            count=len(data),
            loaded=len(data) > 0,
        )
        return result
