"""LifecycleState (Sprint 264).

Program D - Runtime Services & Deployment.
State lifecycle (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass

from . import STATES


@dataclass(frozen=True)
class LifecycleState:
    """State lifecycle (immutable)."""
    name: str
    timestamp: str = "2026-08-01"

    def __post_init__(self) -> None:
        if self.name not in STATES:
            raise ValueError(f"invalid lifecycle state: {self.name}")

    @classmethod
    def created(cls) -> "LifecycleState":
        return cls(name="created")

    @classmethod
    def initializing(cls) -> "LifecycleState":
        return cls(name="initializing")

    @classmethod
    def ready(cls) -> "LifecycleState":
        return cls(name="ready")

    @classmethod
    def running(cls) -> "LifecycleState":
        return cls(name="running")

    @classmethod
    def stopping(cls) -> "LifecycleState":
        return cls(name="stopping")

    @classmethod
    def stopped(cls) -> "LifecycleState":
        return cls(name="stopped")

    @classmethod
    def failed(cls) -> "LifecycleState":
        return cls(name="failed")

    def as_dict(self) -> dict:
        return {"name": self.name, "timestamp": self.timestamp}
