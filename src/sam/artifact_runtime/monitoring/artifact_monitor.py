"""ArtifactMonitor — status representasi artifact (read-only)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactStatus:
    state: str = "ready"
    preview_only: bool = True
    external_calls: int = 0


class ArtifactMonitor:
    """Monitor status artifact. Deterministic & read-only."""

    def status(self) -> ArtifactStatus:
        return ArtifactStatus()
