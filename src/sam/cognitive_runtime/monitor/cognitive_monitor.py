"""Cognitive Monitor — pemantauan status kognitif (Sprint 193)."""
from __future__ import annotations
from dataclasses import dataclass

from ..foundation.cognitive_registry import CognitiveRegistry


@dataclass(frozen=True)
class CognitiveStatus:
    """Status unit kognitif (immutable)."""
    cognitive_id: str
    registered: bool = False
    healthy: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "healthy", self.registered)


class CognitiveMonitor:
    """Monitor kognitif. Read-only, deterministik."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry

    def status(self, cognitive_id: str) -> CognitiveStatus:
        return CognitiveStatus(cognitive_id, self._registry.exists(cognitive_id))

    def all_status(self):
        return [self.status(d.id) for d in self._registry.all()]

    def healthy_count(self) -> int:
        return sum(1 for d in self._registry.all() if self._registry.exists(d.id))
