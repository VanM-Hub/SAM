"""Rollback Request (Sprint 255).

Program C - Real Execution Runtime.
Immutable request untuk rollback. Rollback HANYA metadata, bukan external
world (tidak membatalkan efek di dunia nyata).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class RollbackRequest:
    """Request rollback (immutable)."""
    rollback_id: str
    execution_id: str
    provider_id: str = ""
    operation: str = ""
    reason: str = "metadata rollback"
    mode: str = "rollback"
    scope: str = "metadata"  # hanya metadata, bukan external world

    def as_dict(self) -> dict:
        return {
            "rollback_id": self.rollback_id,
            "execution_id": self.execution_id,
            "provider_id": self.provider_id,
            "operation": self.operation,
            "reason": self.reason,
            "mode": self.mode,
            "scope": self.scope,
        }
