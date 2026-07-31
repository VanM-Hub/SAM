"""Skill Definition — definisi skill (immutable DTO, Sprint 165).

Phase XVI — Skill Runtime.
Definisi menghubungkan desriptor dengan input/output/parameter/constraint.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .skill_input import SkillInput  # noqa: F401
from .skill_output import SkillOutput  # noqa: F401


@dataclass(frozen=True)
class SkillDefinition:
    """Definisi skill (immutable)."""
    definition_id: str
    skill_id: str = ""
    name: str = ""
    description: str = ""
    inputs: List[SkillInput] = field(default_factory=list)
    outputs: List[SkillOutput] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

    @property
    def input_count(self) -> int:
        return len(self.inputs)

    @property
    def output_count(self) -> int:
        return len(self.outputs)
