"""Skill Metadata — metadata skill (immutable DTO, Sprint 164).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class SkillMetadata:
    """Metadata skill (immutable)."""
    skill_id: str
    author: str = ""
    created_at: str = ""
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    readonly: bool = True
