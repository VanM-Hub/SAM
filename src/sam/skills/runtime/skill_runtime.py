"""Skill Runtime — engine runtime skill (Sprint 167).

Phase XVI — Skill Runtime.
Pipeline: Descriptor → Definition → Builder → Workflow → Preview.
Preview-only, external_calls selalu 0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from ..foundation.skill_registry import SkillRegistry
from ..definition.skill_definition import SkillDefinition
from ..builder.skill_builder import SkillBuilder, SkillBuildResult


@dataclass(frozen=True)
class SkillRunResult:
    """Hasil menjalankan pipeline skill (immutable)."""
    skill_id: str
    ok: bool = False
    steps: int = 0
    external_calls: int = 0
    detail: str = ""


class SkillRuntime:
    """Runtime skill. Pipeline preview-only."""

    RUNTIME_VERSION = "1.0.0"

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry
        self._builder = SkillBuilder()

    def pipeline(self, skill_id: str) -> SkillRunResult:
        if not self._registry.exists(skill_id):
            return SkillRunResult(
                skill_id=skill_id, ok=False, detail="skill not registered"
            )
        descriptor = self._registry.find(skill_id)
        built = self._builder.build(skill_id, name=descriptor.name)
        if not built.valid:
            return SkillRunResult(skill_id=skill_id, ok=False, detail="build failed")
        return SkillRunResult(
            skill_id=skill_id, ok=True, steps=1, external_calls=0,
            detail="preview pipeline ready",
        )

    def run(self, skill_id: str) -> SkillRunResult:
        return self.pipeline(skill_id)

    @property
    def registry(self) -> SkillRegistry:
        return self._registry
