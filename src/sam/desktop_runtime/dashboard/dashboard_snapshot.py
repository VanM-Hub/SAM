"""Sprint 275 - Desktop Dashboard: snapshot (immutable)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .card_model import DashboardCard


@dataclass(frozen=True)
class DashboardSnapshot:
    """Snapshot dashboard read-only (hasil komposisi kartu)."""

    dashboard_id: str = "main"
    cards: Tuple[DashboardCard, ...] = ()
    total_size: int = 0

    def __post_init__(self):
        if self.total_size == 0 and self.cards:
            object.__setattr__(
                self, "total_size", sum(c.size for c in self.cards)
            )

    def card_titles(self) -> Tuple[str, ...]:
        return tuple(c.title for c in self.cards)

    def as_dict(self) -> dict:
        return {
            "dashboard_id": self.dashboard_id,
            "cards": [c.as_dict() for c in self.cards],
            "total_size": self.total_size,
        }
