"""RuntimeSnapshot (Sprint 269).

Program D - Runtime Services & Deployment.
Snapshot kondisi runtime (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class RuntimeSnapshot:
    """Snapshot runtime (immutable)."""
    services: Dict[str, str] = field(default_factory=dict)  # name -> status
    version: str = "27.0.0"
    healthy: bool = True
    extra: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "services": dict(self.services),
            "version": self.version,
            "healthy": self.healthy,
            "extra": dict(self.extra),
        }
