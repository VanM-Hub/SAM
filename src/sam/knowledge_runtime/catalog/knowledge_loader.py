"""Knowledge Loader — pemuat knowledge (Sprint 184).

Phase XVIII — Knowledge Runtime.
Load read-only ke registry. Tidak menyimpan ke filesystem/database.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.knowledge_registry import KnowledgeRegistry
from ..foundation.knowledge_descriptor import KnowledgeDescriptor


@dataclass(frozen=True)
class KnowledgeLoadResult:
    """Hasil pemuatan (immutable)."""
    loaded: int = 0
    failed: int = 0
    errors: List[str] = field(default_factory=list)


class KnowledgeLoader:
    """Loader knowledge. Deterministik, read-only."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry

    def load(self, descriptors: List[KnowledgeDescriptor]) -> KnowledgeLoadResult:
        loaded = 0
        failed = 0
        errors = []
        for d in descriptors:
            if self._registry.register(d):
                loaded += 1
            else:
                failed += 1
                errors.append(f"duplicate: {d.id}")
        return KnowledgeLoadResult(loaded=loaded, failed=failed, errors=errors)
