"""Cognitive Registry — registri unit kognitif (Sprint 188)."""
from __future__ import annotations
from typing import Dict, List

from .cognitive_descriptor import CognitiveDescriptor
from .cognitive_capability import CognitiveCapability


class CognitiveRegistry:
    """Registri kognitif. Register/attach hanya untuk komposisi
    in-memory — tidak ada penyimpanan eksternal (no write)."""

    def __init__(self) -> None:
        self._descriptors: Dict[str, CognitiveDescriptor] = {}
        self._capabilities: Dict[str, List[CognitiveCapability]] = {}

    def register(self, descriptor: CognitiveDescriptor) -> None:
        self._descriptors[descriptor.id] = descriptor

    def attach_capability(self, capability: CognitiveCapability) -> None:
        self._capabilities.setdefault(capability.owner_id, []).append(capability)

    def get(self, cognitive_id: str) -> CognitiveDescriptor | None:
        return self._descriptors.get(cognitive_id)

    def exists(self, cognitive_id: str) -> bool:
        return cognitive_id in self._descriptors

    def all(self) -> List[CognitiveDescriptor]:
        return list(self._descriptors.values())

    def count(self) -> int:
        return len(self._descriptors)

    def capabilities(self, cognitive_id: str) -> List[CognitiveCapability]:
        return list(self._capabilities.get(cognitive_id, []))
