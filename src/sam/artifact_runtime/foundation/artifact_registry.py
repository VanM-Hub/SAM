"""ArtifactRegistry — registry artifact immutable in-memory."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Optional

from .artifact_descriptor import ArtifactDescriptor


@dataclass(frozen=True)
class ArtifactRegistry:
    """Registry artifact read-only (pure, register mengembalikan instance baru)."""
    _entries: Tuple[ArtifactDescriptor, ...] = ()

    def register(self, descriptor: ArtifactDescriptor) -> "ArtifactRegistry":
        return ArtifactRegistry(self._entries + (descriptor,))

    def lookup(self, name: str) -> Optional[ArtifactDescriptor]:
        for d in self._entries:
            if d.name == name:
                return d
        return None

    def all(self) -> Tuple[ArtifactDescriptor, ...]:
        return self._entries

    def count(self) -> int:
        return len(self._entries)

    def names(self) -> Tuple[str, ...]:
        return tuple(d.name for d in self._entries)
