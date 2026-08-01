"""Sprint 276 - Desktop Runtime: summary (immutable)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class DesktopSummary:
    """Ringkasan status desktop read-only."""

    runtime: str = "desktop_runtime"
    version: str = "29.0.0"
    panels: Tuple[str, ...] = ()
    dashboard_cards: int = 0
    read_only: bool = True
    execute_self: bool = False

    def as_dict(self) -> dict:
        return {
            "runtime": self.runtime,
            "version": self.version,
            "panels": list(self.panels),
            "dashboard_cards": self.dashboard_cards,
            "read_only": self.read_only,
            "execute_self": self.execute_self,
        }
