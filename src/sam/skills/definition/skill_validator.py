"""Skill Validator — validasi skill definition (Sprint 165).

Phase XVI — Skill Runtime.
Memvalidasi definisi, input, output, konstraint. Deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .skill_definition import SkillDefinition
from .skill_input import SkillInput
from .skill_output import SkillOutput
from .skill_constraint import SkillConstraint


@dataclass(frozen=True)
class SkillValidation:
    """Hasil validasi skill (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class SkillValidator:
    """Validator skill. Deterministik."""

    def validate(self, definition: SkillDefinition) -> SkillValidation:
        issues = []
        if not definition.definition_id:
            issues.append("definition_id required")
        if not definition.skill_id:
            issues.append("skill_id required")
        for inp in definition.inputs:
            if not inp.name:
                issues.append("input name required")
        for out in definition.outputs:
            if not out.name:
                issues.append("output name required")
        return SkillValidation(valid=not issues, issues=issues)

    def validate_inputs(self, inputs: List[SkillInput]) -> SkillValidation:
        issues = []
        for inp in inputs:
            if not inp.name:
                issues.append("input name required")
        return SkillValidation(valid=not issues, issues=issues)

    def validate_outputs(self, outputs: List[SkillOutput]) -> SkillValidation:
        issues = []
        for out in outputs:
            if not out.name:
                issues.append("output name required")
        return SkillValidation(valid=not issues, issues=issues)

    def validate_constraints(
        self, constraints: List[SkillConstraint]
    ) -> SkillValidation:
        issues = []
        for c in constraints:
            if not c.name:
                issues.append("constraint name required")
        return SkillValidation(valid=not issues, issues=issues)
