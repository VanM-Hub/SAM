"""Filesystem Validator — validasi request filesystem (deterministik).

Sprint 145 — Filesystem Provider.
Memvalidasi request preview tanpa akses disk.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .filesystem_request import FilesystemRequest

ALLOWED_OPERATIONS = {
    "read", "write", "copy", "move", "delete",
    "exists", "list", "mkdir", "preview",
}


@dataclass(frozen=True)
class FilesystemValidation:
    """Hasil validasi request filesystem (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class FilesystemValidator:
    """Validator request filesystem. Sinkronus, deterministik."""

    def validate(self, request: FilesystemRequest) -> FilesystemValidation:
        issues = []
        if not request.request_id:
            issues.append("request_id required")
        if request.operation not in ALLOWED_OPERATIONS:
            issues.append(f"unsupported operation: {request.operation}")
        if not request.path:
            issues.append("path required")
        if request.operation == "copy" and not request.target_path:
            issues.append("copy requires target_path")
        if request.operation == "move" and not request.target_path:
            issues.append("move requires target_path")
        return FilesystemValidation(valid=not issues, issues=issues)
