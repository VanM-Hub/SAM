"""Reasoning Validator — validasi struktur reasoning (Sprint 243).

Program B — Model Runtime Integration.
Deterministik, no reasoning, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .reasoning_plan import ReasoningPlan
from .reasoning_summary import ReasoningSummary


@dataclass(frozen=True)
class ReasoningValidation:
    """Hasil validasi (immutable)."""
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"valid": self.valid, "errors": list(self.errors),
                "warnings": list(self.warnings)}


class ReasoningValidator:
    """Validator struktur reasoning. Read-only."""

    VALID_KINDS = ("thought", "observation", "decision")

    def validate_plan(self, plan: ReasoningPlan) -> ReasoningValidation:
        errors: List[str] = []
        if not plan.goal:
            errors.append("goal required")
        for step in plan.steps:
            if step.kind not in self.VALID_KINDS:
                errors.append(f"invalid step kind: {step.kind}")
        if not plan.steps:
            errors.append("plan must have steps")
        return ReasoningValidation(valid=not errors, errors=errors)

    def validate_summary(self, summary: ReasoningSummary) -> ReasoningValidation:
        errors: List[str] = []
        if not summary.goal:
            errors.append("goal required")
        return ReasoningValidation(valid=not errors, errors=errors)
