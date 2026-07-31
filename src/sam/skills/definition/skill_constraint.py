"""Skill Constraint — konstraint skill (immutable DTO, Sprint 165).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class SkillConstraint:
    """Konstraint skill (immutable)."""
    name: str
    description: str = ""
    allowed: bool = True
    reasons: List[str] = field(default_factory=list)
