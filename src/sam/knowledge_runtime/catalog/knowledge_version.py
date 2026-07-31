"""Knowledge Version — versi knowledge (Sprint 184).

Phase XVIII — Knowledge Runtime.
Read-only.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..foundation.knowledge_registry import KnowledgeRegistry


@dataclass(frozen=True)
class KnowledgeVersionInfo:
    """Info versi knowledge (immutable)."""
    knowledge_id: str
    version: str = "1.0.0"
    stable: bool = True


class KnowledgeVersionProvider:
    """Penyedia versi knowledge. Read-only."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry

    def version_of(self, knowledge_id: str) -> str:
        d = self._registry.find(knowledge_id)
        return d.version if d else ""

    def info(self, knowledge_id: str) -> KnowledgeVersionInfo:
        d = self._registry.find(knowledge_id)
        if d is None:
            return KnowledgeVersionInfo(knowledge_id=knowledge_id, version="", stable=False)
        return KnowledgeVersionInfo(knowledge_id=knowledge_id, version=d.version)
