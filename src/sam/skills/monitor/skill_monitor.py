"""Skill Monitor — monitor skill (Sprint 169).

Phase XVI — Skill Runtime.
Memantau status skill. Read-only, deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.skill_registry import SkillRegistry
from ..catalog.skill_version import SkillVersionProvider


@dataclass(frozen=True)
class SkillStatus:
    """Status skill (immutable)."""
    skill_id: str
    registered: bool = False
    has_capability: bool = False
    has_contract: bool = False
    version: str = ""
    healthy: bool = False


class SkillMonitor:
    """Monitor skill. Read-only."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry
        self._version = SkillVersionProvider(registry)

    def status(self, skill_id: str) -> SkillStatus:
        registered = self._registry.exists(skill_id)
        has_cap = bool(self._registry.get_capabilities(skill_id))
        has_contract = self._registry.get_contract(skill_id) is not None
        version = self._version.version_of(skill_id)
        healthy = registered and has_cap
        return SkillStatus(
            skill_id=skill_id, registered=registered,
            has_capability=has_cap, has_contract=has_contract,
            version=version, healthy=healthy,
        )

    def all_status(self) -> List[SkillStatus]:
        return [self.status(sid) for sid in self._registry.list_ids()]

    def healthy_count(self) -> int:
        return sum(1 for s in self.all_status() if s.healthy)
