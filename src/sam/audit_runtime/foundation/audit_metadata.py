"""Audit Metadata — metadata audit (Sprint 212)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class AuditMetadata:
    """Metadata audit immutable."""
    version: str = "22.0.0"
    runtime: str = "audit_runtime"
    phase: str = "XXII"
    immutable: bool = True
    preview_only: bool = True
