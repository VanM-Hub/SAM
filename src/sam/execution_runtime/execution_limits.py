"""Execution Limits (Sprint 257).

Program C - Real Execution Runtime.
Batasan eksekusi yang dievaluasi (immutable result).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class ExecutionLimits:
    """Batasan eksekusi (immutable)."""
    limits_id: str
    execution_id: str
    within_timeout: bool = True
    within_retry_limit: bool = True
    provider_allowed: bool = True
    capability_ok: bool = True
    approved: bool = True

    @property
    def safe(self) -> bool:
        return all((self.within_timeout, self.within_retry_limit,
                    self.provider_allowed, self.capability_ok, self.approved))

    def as_dict(self) -> dict:
        return {"limits_id": self.limits_id, "execution_id": self.execution_id,
                "within_timeout": self.within_timeout,
                "within_retry_limit": self.within_retry_limit,
                "provider_allowed": self.provider_allowed,
                "capability_ok": self.capability_ok,
                "approved": self.approved, "safe": self.safe}
