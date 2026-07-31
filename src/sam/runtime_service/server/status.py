"""ServerStatus (Sprint 268).

Program D - Runtime Services & Deployment.
Status server (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class ServerStatus:
    """Status server (immutable)."""
    name: str
    status: str = "created"
    started: bool = False
    components: Dict[str, str] = field(default_factory=dict)
    version: str = "27.0.0"

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "started": self.started,
            "components": dict(self.components),
            "version": self.version,
        }
