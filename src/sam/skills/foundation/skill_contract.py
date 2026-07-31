"""Skill Contract — kontrak skill (immutable DTO, Sprint 164).

Phase XVI — Skill Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class SkillContract:
    """Kontrak skill (immutable)."""
    contract_id: str
    skill_id: str
    name: str = ""
    guarantees: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SkillContractCompliance:
    """Hasil cek kepatuhan kontrak (immutable)."""
    contract_id: str
    skill_id: str
    compliant: bool = True
    reasons: List[str] = field(default_factory=list)
