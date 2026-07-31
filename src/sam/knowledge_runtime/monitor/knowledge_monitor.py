"""Knowledge Monitor — monitor knowledge (Sprint 185).

Phase XVIII — Knowledge Runtime.
Read-only, deterministic.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.knowledge_registry import KnowledgeRegistry
from ..catalog.knowledge_version import KnowledgeVersionProvider


@dataclass(frozen=True)
class KnowledgeStatus:
    """Status knowledge (immutable)."""
    knowledge_id: str
    registered: bool = False
    has_capability: bool = False
    has_contract: bool = False
    version: str = ""
    healthy: bool = False


class KnowledgeMonitor:
    """Monitor knowledge. Read-only."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry
        self._version = KnowledgeVersionProvider(registry)

    def status(self, knowledge_id: str) -> KnowledgeStatus:
        registered = self._registry.exists(knowledge_id)
        has_cap = bool(self._registry.get_capabilities(knowledge_id))
        has_contract = self._registry.get_contract(knowledge_id) is not None
        version = self._version.version_of(knowledge_id)
        healthy = registered and has_cap
        return KnowledgeStatus(
            knowledge_id=knowledge_id, registered=registered,
            has_capability=has_cap, has_contract=has_contract,
            version=version, healthy=healthy,
        )

    def all_status(self) -> List[KnowledgeStatus]:
        return [self.status(kid) for kid in self._registry.list_ids()]

    def healthy_count(self) -> int:
        return sum(1 for s in self.all_status() if s.healthy)
