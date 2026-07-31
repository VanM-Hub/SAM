"""Embedding Validator — validasi embedding (Sprint 242).

Program B — Model Runtime Integration.
Deterministik, no-network, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .embedding_request import EmbeddingRequest
from .embedding_result import EmbeddingResult


@dataclass(frozen=True)
class EmbeddingValidation:
    """Hasil validasi (immutable)."""
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"valid": self.valid, "errors": list(self.errors),
                "warnings": list(self.warnings)}


class EmbeddingValidator:
    """Validator embedding. Read-only."""

    VALID_INPUT_TYPES = ("search_document", "search_query", "clustering")

    def validate_request(self, request: EmbeddingRequest) -> EmbeddingValidation:
        errors: List[str] = []
        warnings: List[str] = []
        if not request.request_id:
            errors.append("request_id required")
        if not request.texts:
            errors.append("texts cannot be empty")
        if request.input_type not in self.VALID_INPUT_TYPES:
            errors.append(f"invalid input_type: {request.input_type}")
        if request.external_calls != 0:
            warnings.append("external_calls should be 0 in preview")
        return EmbeddingValidation(valid=not errors, errors=errors, warnings=warnings)

    def validate_result(self, result: EmbeddingResult, expected: int) -> EmbeddingValidation:
        errors: List[str] = []
        if len(result.vectors) != expected:
            errors.append("vector count mismatch")
        if result.external_calls != 0:
            errors.append("external_calls must be 0")
        return EmbeddingValidation(valid=not errors, errors=errors)
