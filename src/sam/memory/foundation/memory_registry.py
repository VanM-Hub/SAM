"""Memory Registry — registry memori (Sprint 172).

Phase XVII — Memory Runtime.
register/find/exists/list. Append + read-only query. Deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .memory_descriptor import MemoryDescriptor
from .memory_capability import MemoryCapability
from .memory_contract import MemoryContract
from .memory_metadata import MemoryMetadata


@dataclass(frozen=True)
class MemoryRegistrySummary:
    """Ringkasan registry (immutable)."""
    total: int = 0
    by_category: Dict[str, int] = field(default_factory=dict)


class MemoryRegistry:
    """Registry memori. Append + read-only query."""

    def __init__(self) -> None:
        self._descriptors: Dict[str, MemoryDescriptor] = {}
        self._capabilities: Dict[str, List[MemoryCapability]] = {}
        self._contracts: Dict[str, MemoryContract] = {}
        self._metadata: Dict[str, MemoryMetadata] = {}

    def register(self, descriptor: MemoryDescriptor) -> bool:
        if descriptor.id in self._descriptors:
            return False
        self._descriptors[descriptor.id] = descriptor
        return True

    def attach_capability(self, capability: MemoryCapability) -> bool:
        self._capabilities.setdefault(capability.memory_id, []).append(capability)
        return True

    def attach_contract(self, contract: MemoryContract) -> bool:
        self._contracts[contract.memory_id] = contract
        return True

    def attach_metadata(self, metadata: MemoryMetadata) -> bool:
        self._metadata[metadata.memory_id] = metadata
        return True

    def find(self, memory_id: str) -> Optional[MemoryDescriptor]:
        return self._descriptors.get(memory_id)

    def exists(self, memory_id: str) -> bool:
        return memory_id in self._descriptors

    def list_ids(self) -> List[str]:
        return list(self._descriptors.keys())

    def get_capabilities(self, memory_id: str) -> List[MemoryCapability]:
        return list(self._capabilities.get(memory_id, []))

    def get_contract(self, memory_id: str) -> Optional[MemoryContract]:
        return self._contracts.get(memory_id)

    def get_metadata(self, memory_id: str) -> Optional[MemoryMetadata]:
        return self._metadata.get(memory_id)

    def count(self) -> int:
        return len(self._descriptors)

    def summary(self) -> MemoryRegistrySummary:
        by_cat: Dict[str, int] = {}
        for d in self._descriptors.values():
            by_cat[d.category] = by_cat.get(d.category, 0) + 1
        return MemoryRegistrySummary(total=self.count(), by_category=by_cat)


__all__ = [
    "MemoryRegistry", "MemoryRegistrySummary",
    "MemoryDescriptor", "MemoryCapability",
    "MemoryContract", "MemoryContractCompliance", "MemoryMetadata",
]
