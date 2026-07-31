"""APIHealth (Sprint 267).

Program D - Runtime Services & Deployment.
Health check internal (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class APIHealth:
    """Health check (immutable)."""
    status: str = "healthy"  # healthy | degraded | unhealthy
    checks: List[str] = field(default_factory=list)
    message: str = ""

    def is_healthy(self) -> bool:
        return self.status == "healthy"

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "checks": list(self.checks),
            "message": self.message,
        }
