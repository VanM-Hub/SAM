"""Execution Validation (Sprint 251).

Program C - Real Execution Runtime.
Validasi request sebelum eksekusi (statis, deterministic, no network).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .execution_request import ExecutionRequest


@dataclass(frozen=True)
class ExecutionValidation:
    """Hasil validasi eksekusi (immutable)."""
    validation_id: str
    execution_id: str
    valid: bool
    errors: tuple = field(default_factory=tuple)
    warnings: tuple = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "validation_id": self.validation_id,
            "execution_id": self.execution_id,
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


class ExecutionValidationEngine:
    """Validasi request eksekusi. Read-only, deterministic."""

    def validate(self, validation_id: str, request: ExecutionRequest) -> ExecutionValidation:
        errors: List[str] = []
        warnings: List[str] = []
        if request.execution_id != request.execution_id:
            errors.append("execution_id inconsistent")
        if request.provider_id == "":
            errors.append("provider_id required")
        if request.operation == "":
            errors.append("operation required")
        if not request.deterministic:
            warnings.append("non-deterministic request")
        if request.max_retries > 5:
            warnings.append("high retry count")
        if request.mode == "execute" and not request.approved:
            warnings.append("execute without approval")
        return ExecutionValidation(
            validation_id=validation_id,
            execution_id=request.execution_id,
            valid=len(errors) == 0,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )
