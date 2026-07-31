"""Cognitive Snapshot — snapshot konteks kognitif (Sprint 189)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict

from .cognitive_context import CognitiveContext


@dataclass(frozen=True)
class CognitiveSnapshot:
    """Snapshot konteks kognitif (immutable)."""
    snapshot_id: str = ""
    context: CognitiveContext = field(default_factory=CognitiveContext)
    created_at: str = ""
    sources: List[str] = field(default_factory=list)

    def total_entries(self) -> int:
        return self.context.entry_count()
