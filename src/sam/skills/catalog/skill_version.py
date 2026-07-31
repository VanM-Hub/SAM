"""Skill Version — versi skill (Sprint 168).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.skill_registry import SkillRegistry


@dataclass(frozen=True)
class SkillVersionInfo:
    """Info versi skill (immutable)."""
    skill_id: str
    version: str = "1.0.0"
    stable: bool = True


class SkillVersionProvider:
    """Penyedia versi skill. Read-only."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def version_of(self, skill_id: str) -> str:
        d = self._registry.find(skill_id)
        return d.version if d else ""

    def info(self, skill_id: str) -> SkillVersionInfo:
        d = self._registry.find(skill_id)
        if d is None:
            return SkillVersionInfo(skill_id=skill_id, version="", stable=False)
        return SkillVersionInfo(skill_id=skill_id, version=d.version)
