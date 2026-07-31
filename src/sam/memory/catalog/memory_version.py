"""Memory Version — versi memori (Sprint 176).

Phase XVII — Memory Runtime.
Read-only.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..foundation.memory_registry import MemoryRegistry


@dataclass(frozen=True)
class MemoryVersionInfo:
    """Info versi memori (immutable)."""
    memory_id: str
    version: str = "1.0.0"
    stable: bool = True


class MemoryVersionProvider:
    """Penyedia versi memori. Read-only."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry

    def version_of(self, memory_id: str) -> str:
        d = self._registry.find(memory_id)
        return d.version if d else ""

    def info(self, memory_id: str) -> MemoryVersionInfo:
        d = self._registry.find(memory_id)
        if d is None:
            return MemoryVersionInfo(memory_id=memory_id, version="", stable=False)
        return MemoryVersionInfo(memory_id=memory_id, version=d.version)
