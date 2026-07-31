"""Audit Summary — ringkasan audit (Sprint 215)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.audit_registry import AuditRegistry


@dataclass(frozen=True)
class AuditSummary:
    """Ringkasan immutable."""
    total: int = 0
    categories: tuple = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "categories", tuple(self.categories))


class AuditSummarizer:
    """Summarizer audit read-only."""

    def summarize(self, registry: AuditRegistry) -> AuditSummary:
        cats = sorted({a.category for a in registry.all_entries()})
        return AuditSummary(total=registry.count(), categories=cats)
