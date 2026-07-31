"""APIStatus (Sprint 267).

Program D - Runtime Services & Deployment.
Status runtime (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class APIStatus:
    """Status runtime (immutable)."""
    services: Dict[str, str] = field(default_factory=dict)
    version: str = "27.0.0"
    healthy: bool = True

    def as_dict(self) -> dict:
        return {
            "services": dict(self.services),
            "version": self.version,
            "healthy": self.healthy,
        }
