"""Cognitive Health — kesehatan runtime kognitif (Sprint 193)."""
from __future__ import annotations
from dataclasses import dataclass

from ..foundation.cognitive_registry import CognitiveRegistry


@dataclass(frozen=True)
class CognitiveHealth:
    """Kesehatan kognitif (immutable)."""
    total: int = 0
    healthy_cognitive: int = 0

    @property
    def healthy(self) -> bool:
        return self.healthy_cognitive == self.total


class CognitiveHealthCheck:
    """Health check kognitif. Read-only."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry

    def check(self) -> CognitiveHealth:
        total = self._registry.count()
        healthy = sum(1 for d in self._registry.all() if self._registry.exists(d.id))
        return CognitiveHealth(total=total, healthy_cognitive=healthy)
