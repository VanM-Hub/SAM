"""Skill Engine — engine skill runtime (Sprint 167).

Phase XVI — Skill Runtime.
Engine facade. Preview-only, deterministic.
"""
from __future__ import annotations
from dataclasses import dataclass

from .skill_runtime import SkillRuntime, SkillRunResult


@dataclass(frozen=True)
class SkillEngineInfo:
    """Info engine skill (immutable)."""
    version: str
    preview_only: bool = True
    deterministic: bool = True


class SkillEngine:
    """Engine skill. Preview-only facade."""

    VERSION = "1.0.0"

    def __init__(self, runtime: SkillRuntime) -> None:
        self._runtime = runtime

    def info(self) -> SkillEngineInfo:
        return SkillEngineInfo(version=self.VERSION)

    def run(self, skill_id: str) -> SkillRunResult:
        return self._runtime.run(skill_id)

    def health(self) -> bool:
        return True
