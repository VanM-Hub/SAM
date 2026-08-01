"""Sprint 275 - Desktop Dashboard: composer (service, tanpa IO)."""
from __future__ import annotations

from typing import Tuple

from .card_model import DashboardCard


class DashboardComposer:
    """Menyusun kartu menjadi dashboard (service murni, deklaratif)."""

    @staticmethod
    def compose(cards: Tuple[DashboardCard, ...]) -> Tuple[DashboardCard, ...]:
        # komposisi deterministik: urutkan stabil, tanpa eksekusi
        return tuple(sorted(cards, key=lambda c: c.title))

    @staticmethod
    def compact(cards: Tuple[DashboardCard, ...]) -> int:
        return sum(c.size for c in cards)

    @staticmethod
    def pick(cards: Tuple[DashboardCard, ...], *titles: str) -> Tuple[DashboardCard, ...]:
        wanted = set(titles)
        return tuple(c for c in cards if c.title in wanted)
