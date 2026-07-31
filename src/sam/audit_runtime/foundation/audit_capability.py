"""Audit Capability — kapabilitas audit (Sprint 212)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class AuditCapability:
    """Kapabilitas audit immutable. Read-only, tanpa eksekusi."""
    name: str = "audit"
    immutable_record: bool = True
    preview_only: bool = True
    no_execute: bool = True
    deterministic: bool = True
