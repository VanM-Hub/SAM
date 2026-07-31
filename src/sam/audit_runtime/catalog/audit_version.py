"""Audit Version — versi audit (Sprint 216)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class AuditVersionInfo:
    """Info versi immutable."""
    version: str = "1.0.0"
    runtime_version: str = "22.0.0"
    immutable: bool = True


class AuditVersionProvider:
    """Provider versi audit read-only."""

    def get(self) -> AuditVersionInfo:
        return AuditVersionInfo()
