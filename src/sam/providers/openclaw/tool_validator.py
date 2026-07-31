"""OpenClaw Tool Validator — validasi request tool (deterministik).

Sprint 149 — OpenClaw Provider.
Memvalidasi request tool tanpa invoke.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .tool_request import OpenClawToolRequest


@dataclass(frozen=True)
class OpenClawToolValidation:
    """Hasil validasi request tool (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class OpenClawToolValidator:
    """Validator request tool. Deterministik, build-only."""

    def validate(self, request: OpenClawToolRequest) -> OpenClawToolValidation:
        issues = []
        if not request.request_id:
            issues.append("request_id required")
        if not request.tool:
            issues.append("tool required")
        return OpenClawToolValidation(valid=not issues, issues=issues)
