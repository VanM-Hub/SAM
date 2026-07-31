"""Audit Registry — registri audit (Sprint 212).

Read-only in-memory registry. Tidak menyimpan, tidak menulis disk.
Sumber audit/provenance deterministik — tanpa penyimpanan maupun eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .audit_descriptor import AuditDescriptor


@dataclass(frozen=True)
class AuditRegistry:
    """Registri audit immutable. Registry in-memory."""
    _entries: Dict[str, AuditDescriptor] = field(default_factory=dict, repr=False)

    def register(self, audit: AuditDescriptor) -> "AuditRegistry":
        return AuditRegistry(_entries={**self._entries, audit.audit_id: audit})

    def get(self, audit_id: str) -> AuditDescriptor:
        return self._entries.get(audit_id)

    def exists(self, audit_id: str) -> bool:
        return audit_id in self._entries

    def count(self) -> int:
        return len(self._entries)

    def all_entries(self) -> List[AuditDescriptor]:
        return list(self._entries.values())

    @classmethod
    def empty(cls) -> "AuditRegistry":
        return cls()
