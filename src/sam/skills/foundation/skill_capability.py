"""Skill Capability — kapabilitas skill (immutable DTO, Sprint 164).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class SkillCapability:
    """Kapabilitas skill (immutable). Preview-only default."""
    capability_id: str
    skill_id: str
    name: str = ""
    category: str = "skill"
    operations: List[str] = field(default_factory=list)
    preview_only: bool = True

    def supports(self, operation: str) -> bool:
        return operation in self.operations
