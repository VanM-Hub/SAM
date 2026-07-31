"""Preview Validator — engine validasi preview.

Sprint 119 — Connector Preview.
Memastikan preview selalu dry-run & tanpa panggilan eksternal.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .preview_request import PreviewRequest


@dataclass(frozen=True)
class PreviewValidationReport:
    preview_id: str
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class PreviewValidator:
    """Validasi permintaan preview — pastikan aman (dry-run)."""

    def validate(self, request: PreviewRequest) -> PreviewValidationReport:
        issues = []
        if not request.dry_run:
            issues.append("dry_run must be True (preview-only)")
        if request.operation not in ("read", "write", "stream", "transform"):
            issues.append(f"unknown operation: {request.operation}")
        return PreviewValidationReport(request.preview_id, not issues, issues)
