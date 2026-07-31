"""Skill Registry — registry skill (Sprint 164).

Phase XVI — Skill Runtime.
Register, find, list, exists. Append + read-only query. Deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .skill_descriptor import SkillDescriptor
from .skill_capability import SkillCapability
from .skill_contract import SkillContract
from .skill_metadata import SkillMetadata


@dataclass(frozen=True)
class SkillRegistrySummary:
    """Ringkasan registry (immutable)."""
    total: int = 0
    by_category: Dict[str, int] = field(default_factory=dict)


class SkillRegistry:
    """Registry skill. Append + read-only query."""

    def __init__(self) -> None:
        self._descriptors: Dict[str, SkillDescriptor] = {}
        self._capabilities: Dict[str, List[SkillCapability]] = {}
        self._contracts: Dict[str, SkillContract] = {}
        self._metadata: Dict[str, SkillMetadata] = {}

    def register(self, descriptor: SkillDescriptor) -> bool:
        if descriptor.id in self._descriptors:
            return False
        self._descriptors[descriptor.id] = descriptor
        return True

    def attach_capability(self, capability: SkillCapability) -> bool:
        self._capabilities.setdefault(capability.skill_id, []).append(capability)
        return True

    def attach_contract(self, contract: SkillContract) -> bool:
        self._contracts[contract.skill_id] = contract
        return True

    def attach_metadata(self, metadata: SkillMetadata) -> bool:
        self._metadata[metadata.skill_id] = metadata
        return True

    def find(self, skill_id: str) -> Optional[SkillDescriptor]:
        return self._descriptors.get(skill_id)

    def list_ids(self) -> List[str]:
        return list(self._descriptors.keys())

    def exists(self, skill_id: str) -> bool:
        return skill_id in self._descriptors

    def get_capabilities(self, skill_id: str) -> List[SkillCapability]:
        return list(self._capabilities.get(skill_id, []))

    def get_contract(self, skill_id: str) -> Optional[SkillContract]:
        return self._contracts.get(skill_id)

    def get_metadata(self, skill_id: str) -> Optional[SkillMetadata]:
        return self._metadata.get(skill_id)

    def count(self) -> int:
        return len(self._descriptors)

    def summary(self) -> SkillRegistrySummary:
        by_cat: Dict[str, int] = {}
        for d in self._descriptors.values():
            by_cat[d.category] = by_cat.get(d.category, 0) + 1
        return SkillRegistrySummary(total=self.count(), by_category=by_cat)


__all__ = [
    "SkillRegistry", "SkillRegistrySummary",
    "SkillDescriptor", "SkillCapability",
    "SkillContract", "SkillContractCompliance", "SkillMetadata",
]
