"""Skill Validator — validasi skill runtime (Sprint 170).

Phase XVI — Skill Runtime.
Memvalidasi kepatuhan terhadap konstrain.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class SkillValidation:
    """Hasil validasi skill (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class SkillValidator:
    """Validator skill. Deterministik."""

    def validate(
        self,
        frozen: bool = True,
        synchronous: bool = True,
        preview_only: bool = True,
        no_execution: bool = True,
        no_forbidden_imports: bool = True,
    ) -> SkillValidation:
        issues = []
        if not frozen:
            issues.append("DTO not frozen")
        if not synchronous:
            issues.append("not synchronous")
        if not preview_only:
            issues.append("not preview-only")
        if not no_execution:
            issues.append("execution detected")
        if not no_forbidden_imports:
            issues.append("forbidden imports detected")
        return SkillValidation(valid=not issues, issues=issues)
