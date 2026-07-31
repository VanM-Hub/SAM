"""Cognitive Snapshot Report — laporan snapshot kognitif (Sprint 193)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from ..foundation.cognitive_registry import CognitiveRegistry


@dataclass(frozen=True)
class CognitiveSnapshot:
    """Snapshot kognitif (immutable). Nama unik untuk sprint 193."""
    total: int = 0
    scope_counts: Dict[str, int] = field(default_factory=dict)


class CognitiveSnapshotter:
    """Snapshotter kognitif. Read-only."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry

    def snapshot(self) -> CognitiveSnapshot:
        descs = self._registry.all()
        counts = {}
        for d in descs:
            counts[d.category] = counts.get(d.category, 0) + 1
        return CognitiveSnapshot(total=len(descs), scope_counts=counts)
