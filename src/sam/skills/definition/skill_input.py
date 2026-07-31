"""Skill Input — input skill (immutable DTO, Sprint 165).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SkillInput:
    """Input skill (immutable)."""
    name: str
    input_type: str = "string"
    required: bool = False
    default: Optional[object] = None
    description: str = ""
