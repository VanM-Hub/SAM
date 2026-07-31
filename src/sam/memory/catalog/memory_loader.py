"""Memory Loader — pemuat memori (Sprint 176).

Phase XVII — Memory Runtime.
Load read-only ke registry. Tidak menyimpan ke filesystem/database.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.memory_registry import MemoryRegistry
from ..foundation.memory_descriptor import MemoryDescriptor


@dataclass(frozen=True)
class MemoryLoadResult:
    """Hasil pemuatan (immutable)."""
    loaded: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)


class MemoryLoader:
    """Loader memori. Deterministik, read-only."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry

    def load(self, descriptors: List[MemoryDescriptor]) -> MemoryLoadResult:
        loaded = 0
        failed = 0
        errors = []
        for d in descriptors:
            if self._registry.register(d):
                loaded += 1
            else:
                failed += 1
                errors.append(f"duplicate: {d.id}")
        return MemoryLoadResult(loaded=loaded, failed=failed, errors=errors)
