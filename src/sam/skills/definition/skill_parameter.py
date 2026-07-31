"""Skill Parameter — parameter skill (immutable DTO, Sprint 165).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass(frozen=True)
class SkillParameter:
    """Parameter skill (immutable)."""
    name: str
    param_type: str = "string"
    required: bool = False
    default: Optional[Any] = None
    allowed_values: List[Any] = field(default_factory=list)
