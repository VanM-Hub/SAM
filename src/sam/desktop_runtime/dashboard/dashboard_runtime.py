"""Sprint 275 - Desktop Dashboard: runtime (composition-only).

Class service (bukan DTO). Setelah konstruksi read-only; tidak menyimpan
state mutabel dan tidak melakukan IO/eksekusi.
"""
from __future__ import annotations

from typing import Tuple

from .card_model import DashboardCard
from .dashboard_composer import DashboardComposer
from .dashboard_snapshot import DashboardSnapshot


class DashboardRuntime:
    """Dashboard Runtime: menyusun kartu menjadi snapshot dashboard."""

    def __init__(self, cards: Tuple[DashboardCard, ...] = ()):
        self._cards = tuple(cards)
        self._locked = True

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False):
            raise AttributeError(f"DashboardRuntime is immutable: {name}")
        super().__setattr__(name, value)

    @property
    def cards(self) -> Tuple[DashboardCard, ...]:
        return self._cards

    def run(self) -> DashboardSnapshot:
        ordered = DashboardComposer.compose(self._cards)
        return DashboardSnapshot(dashboard_id="main", cards=ordered)

    def as_dict(self) -> dict:
        return {
            "runtime": "DashboardRuntime",
            "preview_only": True,
            "execute_self": False,
            "cards": [c.as_dict() for c in self._cards],
        }
