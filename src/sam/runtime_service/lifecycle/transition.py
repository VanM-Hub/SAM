"""LifecycleTransition (Sprint 264).

Program D - Runtime Services & Deployment.
Transisi antar state lifecycle (validasi deterministik).
"""
from __future__ import annotations
from dataclasses import dataclass

from .state import LifecycleState

# Transisi legal (dari -> ke)
_TRANSITIONS = {
    "created": ("initializing", "stopped", "failed"),
    "initializing": ("ready", "failed", "stopped"),
    "ready": ("running", "stopped", "failed"),
    "running": ("stopping", "stopped", "failed"),
    "stopping": ("stopped", "failed"),
    "stopped": (),
    "failed": (),
}


@dataclass(frozen=True)
class LifecycleTransition:
    """Transisi lifecycle (immutable)."""
    source: LifecycleState
    target: LifecycleState

    def is_valid(self) -> bool:
        if self.source.name == self.target.name:
            return False
        return self.target.name in _TRANSITIONS.get(self.source.name, ())
