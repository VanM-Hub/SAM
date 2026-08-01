"""Sprint 277 - Desktop Monitoring: health (immutable)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PresentationHealth:
    """Status kesehatan desktop read-only (deklaratif)."""

    status: str = "healthy"  # healthy | degraded | offline
    checks: Tuple[str, ...] = ()

    def is_healthy(self) -> bool:
        return self.status == "healthy"

    def with_check(self, check: str, healthy: bool = True) -> "PresentationHealth":
        # hanya metadata; tidak melakukan probe IO
        return PresentationHealth(
            status=self.status,
            checks=self.checks + (check,),
        )

    def as_dict(self) -> dict:
        return {
            "status": self.status,
            "checks": list(self.checks),
        }
