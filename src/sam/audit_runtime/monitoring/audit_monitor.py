"""Audit Monitor — pemantauan audit (Sprint 217)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class AuditStatus:
    """Status audit immutable."""
    state: str = "ready"
    immutable: bool = True
    preview_only: bool = True

    def __post_init__(self) -> None:
        if self.state not in ("ready", "observing", "error"):
            raise ValueError(f"invalid state: {self.state}")


class AuditMonitor:
    """Monitor audit read-only."""

    def status(self) -> AuditStatus:
        return AuditStatus()
