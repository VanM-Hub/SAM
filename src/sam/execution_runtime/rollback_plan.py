"""Rollback Plan (Sprint 255).

Program C - Real Execution Runtime.
Rencana rollback immutable: apa yang akan dipulihkan (metadata saja).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .rollback_request import RollbackRequest


@dataclass(frozen=True)
class RollbackPlan:
    """Rencana rollback metadata (immutable)."""
    plan_id: str
    request: RollbackRequest
    metadata_keys: tuple = field(default_factory=tuple)
    scope: str = "metadata"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "request": self.request.as_dict(),
            "metadata_keys": list(self.metadata_keys),
            "scope": self.scope,
            "external_calls": self.external_calls,
        }
