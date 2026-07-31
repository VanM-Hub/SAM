"""Skill Output — output skill (immutable DTO, Sprint 165).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class SkillOutput:
    """Output skill (immutable)."""
    name: str
    output_type: str = "string"
    description: str = ""
