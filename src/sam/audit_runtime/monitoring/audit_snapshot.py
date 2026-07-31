"""Audit Snapshot — snapshot audit (Sprint 217)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.audit_descriptor import AuditDescriptor


@dataclass(frozen=True)
class AuditSnapshot:
    """Snapshot immutable."""
    total: int = 0
    categories: tuple = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "categories", tuple(self.categories))


class AuditSnapshotter:
    """Snapshotter audit read-only."""

    def snapshot(self, audits: List[AuditDescriptor]) -> AuditSnapshot:
        cats = sorted({a.category for a in audits})
        return AuditSnapshot(total=len(audits), categories=cats)
