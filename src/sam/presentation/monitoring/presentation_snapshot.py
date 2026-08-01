"""Sprint 277 - Desktop Monitoring: snapshot (immutable)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PresentationSnapshot:
    """Snapshot monitoring desktop (tunggal, read-only)."""

    runtime: str = "presentation"
    version: str = "29.0.0"
    panels: Tuple[str, ...] = ()
    status: str = "idle"

    def with_status(self, status: str) -> "PresentationSnapshot":
        return PresentationSnapshot(
            runtime=self.runtime,
            version=self.version,
            panels=self.panels,
            status=status,
        )

    def as_dict(self) -> dict:
        return {
            "runtime": self.runtime,
            "version": self.version,
            "panels": list(self.panels),
            "status": self.status,
        }
