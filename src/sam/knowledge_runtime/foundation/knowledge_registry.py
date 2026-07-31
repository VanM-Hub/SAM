"""Knowledge Registry — registry knowledge (Sprint 180).

Phase XVIII — Knowledge Runtime.
register/find/exists/list. Append + read-only query. Deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .knowledge_descriptor import KnowledgeDescriptor
from .knowledge_capability import KnowledgeCapability
from .knowledge_contract import KnowledgeContract
from .knowledge_metadata import KnowledgeMetadata


@dataclass(frozen=True)
class KnowledgeRegistrySummary:
    """Ringkasan registry (immutable)."""
    total: int = 0
    by_category: Dict[str, int] = field(default_factory=dict)


class KnowledgeRegistry:
    """Registry knowledge. Append + read-only query."""

    def __init__(self) -> None:
        self._descriptors: Dict[str, KnowledgeDescriptor] = {}
        self._capabilities: Dict[str, List[KnowledgeCapability]] = {}
        self._contracts: Dict[str, KnowledgeContract] = {}
        self._metadata: Dict[str, KnowledgeMetadata] = {}

    def register(self, descriptor: KnowledgeDescriptor) -> bool:
        if descriptor.id in self._descriptors:
            return False
        self._descriptors[descriptor.id] = descriptor
        return True

    def attach_capability(self, capability: KnowledgeCapability) -> bool:
        self._capabilities.setdefault(capability.knowledge_id, []).append(capability)
        return True

    def attach_contract(self, contract: KnowledgeContract) -> bool:
        self._contracts[contract.knowledge_id] = contract
        return True

    def attach_metadata(self, metadata: KnowledgeMetadata) -> bool:
        self._metadata[metadata.knowledge_id] = metadata
        return True

    def find(self, knowledge_id: str) -> Optional[KnowledgeDescriptor]:
        return self._descriptors.get(knowledge_id)

    def exists(self, knowledge_id: str) -> bool:
        return knowledge_id in self._descriptors

    def list_ids(self) -> List[str]:
        return list(self._descriptors.keys())

    def get_capabilities(self, knowledge_id: str) -> List[KnowledgeCapability]:
        return list(self._capabilities.get(knowledge_id, []))

    def get_contract(self, knowledge_id: str) -> Optional[KnowledgeContract]:
        return self._contracts.get(knowledge_id)

    def get_metadata(self, knowledge_id: str) -> Optional[KnowledgeMetadata]:
        return self._metadata.get(knowledge_id)

    def count(self) -> int:
        return len(self._descriptors)

    def summary(self) -> KnowledgeRegistrySummary:
        by_cat: Dict[str, int] = {}
        for d in self._descriptors.values():
            by_cat[d.category] = by_cat.get(d.category, 0) + 1
        return KnowledgeRegistrySummary(total=self.count(), by_category=by_cat)


__all__ = [
    "KnowledgeRegistry", "KnowledgeRegistrySummary",
    "KnowledgeDescriptor", "KnowledgeCapability",
    "KnowledgeContract", "KnowledgeContractCompliance", "KnowledgeMetadata",
]
