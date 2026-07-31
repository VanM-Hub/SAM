"""Memory Snapshot — snapshot memori (Sprint 177).

Phase XVII — Memory Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from ..foundation.memory_registry import MemoryRegistry


@dataclass(frozen=True)
class MemorySnapshot:
    """Snapshot memori (immutable)."""
    memory_id: str = ""
    total: int = 0
    categories: Dict[str, int] = field(default_factory=dict)


class MemorySnapshotter:
    """Pembuat snapshot memori. Read-only."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry

    def snapshot(self) -> MemorySnapshot:
        s = self._registry.summary()
        return MemorySnapshot(
            memory_id="all", total=s.total, categories=s.by_category,
        )
