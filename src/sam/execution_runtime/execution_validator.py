"""Execution Validator (Sprint 258).

Program C - Real Execution Runtime.
Validasi struktur execution runtime (immutable, no network).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .execution_request import ExecutionRequest


@dataclass(frozen=True)
class ExecutionValidatorResult:
    """Hasil validasi (immutable)."""
    valid: bool
    errors: tuple = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"valid": self.valid, "errors": list(self.errors)}


class ExecutionValidator:
    """Validasi request eksekusi. Deterministic, read-only."""

    def validate(self, request: ExecutionRequest) -> ExecutionValidatorResult:
        errors: List[str] = []
        if not request.execution_id:
            errors.append("execution_id required")
        if not request.provider_id:
            errors.append("provider_id required")
        if not request.operation:
            errors.append("operation required")
        if request.timeout_seconds < 1:
            errors.append("timeout must be >= 1")
        return ExecutionValidatorResult(valid=len(errors) == 0, errors=tuple(errors))
