"""Sprint 277 - Desktop Monitoring: report (immutable)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class DesktopReport:
    """Laporan monitoring desktop read-only."""

    observations: Tuple[str, ...] = ()
    counters: Dict[str, int] = field(default_factory=dict)
    status: str = "ok"

    def with_observation(self, text: str) -> "DesktopReport":
        return DesktopReport(
            observations=self.observations + (text,),
            counters=self.counters,
            status=self.status,
        )

    def as_dict(self) -> dict:
        return {
            "observations": list(self.observations),
            "counters": dict(self.counters),
            "status": self.status,
        }
