"""Translation Validator — engine validasi terjemahan.

Sprint 118 — Connector Translation.
Validasi permintaan terjemahan (read-only).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .translation_request import TranslationRequest


@dataclass(frozen=True)
class TranslationValidationReport:
    request_id: str
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class TranslationValidator:
    """Validasi permintaan terjemahan."""

    def validate(self, request: TranslationRequest) -> TranslationValidationReport:
        issues = []
        if not request.request_id.strip():
            issues.append("request_id empty")
        if not request.payload:
            issues.append("empty payload")
        return TranslationValidationReport(request.request_id, not issues, issues)
