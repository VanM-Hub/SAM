"""Model Validator — validasi generik model (Sprint 240).

Program B — Model Runtime Integration.
Deterministik, no-network, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .model_request import ModelRequest
from .model_response import ModelResponse
from .model_message import ModelMessage


@dataclass(frozen=True)
class ModelValidationResult:
    """Hasil validasi (immutable)."""
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


class ModelValidator:
    """Validator generik request/response model. Read-only, deterministik."""

    VALID_TASKS = ("chat", "embedding", "reasoning", "vision", "tool")
    VALID_MODES = ("preview", "approval", "execute")

    def validate_request(self, request: ModelRequest) -> ModelValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        if not request.request_id:
            errors.append("request_id required")
        if request.task not in self.VALID_TASKS:
            errors.append(f"invalid task: {request.task}")
        if request.model_type not in self.VALID_TASKS:
            errors.append(f"invalid model_type: {request.model_type}")
        if request.mode not in self.VALID_MODES:
            errors.append(f"invalid mode: {request.mode}")
        if request.external_calls != 0:
            warnings.append("external_calls should be 0 in preview")
        for message in request.context.messages:
            if message.role not in ("system", "user", "assistant", "tool"):
                errors.append(f"invalid role: {message.role}")
        return ModelValidationResult(valid=not errors, errors=errors, warnings=warnings)

    def validate_response(self, response: ModelResponse) -> ModelValidationResult:
        errors: List[str] = []
        if not response.response_id:
            errors.append("response_id required")
        if not response.request_id:
            errors.append("request_id required")
        if response.external_calls != 0:
            errors.append("external_calls must be 0 in preview")
        return ModelValidationResult(valid=not errors, errors=errors)
