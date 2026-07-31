"""Cognitive Validator — validasi konteks kognitif (Sprint 189)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .cognitive_context import CognitiveContext
from .cognitive_scope import CognitiveScope, VALID_SCOPES
from .cognitive_reference import CognitiveReference


@dataclass(frozen=True)
class CognitiveValidation:
    """Hasil validasi (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class CognitiveValidator:
    """Validator konteks kognitif. Deterministik, read-only."""

    def validate_context(self, context: CognitiveContext) -> CognitiveValidation:
        issues = []
        if not context.cognitive_id:
            issues.append("cognitive_id is required")
        if context.scope not in VALID_SCOPES:
            issues.append(f"invalid scope '{context.scope}'")
        return CognitiveValidation(valid=not issues, issues=issues)

    def validate_scope(self, scope: CognitiveScope) -> CognitiveValidation:
        issues = []
        if scope.scope not in VALID_SCOPES:
            issues.append(f"invalid scope '{scope.scope}'")
        return CognitiveValidation(valid=not issues, issues=issues)

    def validate_reference(self, ref: CognitiveReference) -> CognitiveValidation:
        issues = []
        if not ref.runtime:
            issues.append("runtime is required")
        return CognitiveValidation(valid=not issues, issues=issues)
