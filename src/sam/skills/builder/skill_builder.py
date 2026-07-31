"""Skill Builder — membangun skill DTO (Sprint 166).

Phase XVI — Skill Runtime.
Builder hanya membangun DTO. Tidak memilih runtime, tidak execute.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from ..foundation.skill_descriptor import SkillDescriptor
from ..definition.skill_definition import SkillDefinition


@dataclass(frozen=True)
class SkillBuildResult:
    """Hasil pembangunan skill (immutable)."""
    descriptor: Optional[SkillDescriptor] = None
    definition: Optional[SkillDefinition] = None
    valid: bool = False
    reason: str = ""


class SkillBuilder:
    """Builder skill. Deterministik, build-only."""

    def build(
        self,
        skill_id: str,
        name: str = "",
        category: str = "general",
        version: str = "1.0.0",
        description: str = "",
        author: str = "",
        tags: List[str] = None,
    ) -> SkillBuildResult:
        if not skill_id:
            return SkillBuildResult(valid=False, reason="skill_id required")
        descriptor = SkillDescriptor(
            id=skill_id, name=name or skill_id, version=version,
            category=category, description=description, author=author,
            tags=list(tags or []),
        )
        definition = SkillDefinition(
            definition_id=f"def.{skill_id}", skill_id=skill_id, name=name or skill_id,
        )
        return SkillBuildResult(
            descriptor=descriptor, definition=definition, valid=True,
        )
