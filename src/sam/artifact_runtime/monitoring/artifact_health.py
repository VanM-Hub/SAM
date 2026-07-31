"""ArtifactHealth — kesehatan representasi artifact (read-only)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactHealth:
    healthy: bool = True
    external_calls: int = 0


class ArtifactHealthCheck:
    """Pemeriksa kesehatan artifact. Deterministic & read-only."""

    def check(self) -> ArtifactHealth:
        return ArtifactHealth()
