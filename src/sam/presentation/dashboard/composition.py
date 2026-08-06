"""ENG-H-001 (AP-MISSION-003-001) — G1 Dashboard Structure: UI Composition.

Program H — Dashboard. Komposisi UI menggabungkan ViewModel + DTO
deklaratif lama (DashboardCard/DashboardComposer, Sprint 275) menjadi
satu pandangan Dashboard yang siap dibungkus lapisan di atasnya.
Hanya menyusun; TIDAK mengeksekusi dan TIDAK memanggil subsystem.
Konsisten dengan Composition Principle (Art. XVI) dan pola Sprint 276
(service composition-only + DTO immutable).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .card_model import DashboardCard
from .dashboard_composer import DashboardComposer
from .viewmodel import DashboardPanel, DashboardViewModel


@dataclass(frozen=True)
class DashboardComposition:
    """Komposisi UI Dashboard (View + panel + kartu terurut). Read-only."""

    viewmodel: DashboardViewModel = field(default_factory=DashboardViewModel)
    cards: Tuple[DashboardCard, ...] = ()
    panel_specs: Tuple[Dict, ...] = ()

    def as_dict(self) -> dict:
        return {
            "dashboard": self.viewmodel.as_dict(),
            "cards": [c.as_dict() for c in self.cards],
            "panels": list(self.panel_specs),
        }


def _panel_to_card(panel: DashboardPanel, index: int) -> DashboardCard:
    """Petakan satu panel -> DashboardCard deklaratif (composition-only)."""
    title = panel.area.capitalize()
    return DashboardCard(
        title=title,
        source_runtime=panel.source,
        kind="panel",
        size=index,
        sections=panel.sections,
    )


def compose_dashboard(
    viewmodel: DashboardViewModel,
    panels: Tuple[DashboardPanel, ...] | None = None,
) -> DashboardComposition:
    """Susun komposisi UI Dashboard dari ViewModel (composition-only).

    Menggabungkan panel activated (status ready/limited) menjadi kartu
    terurut via DashboardComposer; area missing tetap direpresentasikan
    sebagai panel dengan status (tanpa kartu eksekusi).
    """
    sources = tuple(viewmodel.panels) if panels is None else tuple(panels)
    visible = [p for p in sources if p.status in ("ready", "limited", "detached")]
    missing = [p for p in sources if p.status == "missing"]

    cards = [panel_to_card(p, i + 1) for i, p in enumerate(visible)]
    ordered = DashboardComposer.compose(cards)

    specs = [p.as_dict() for p in sources]
    return DashboardComposition(
        viewmodel=viewmodel, cards=ordered, panel_specs=specs
    )


# alias ringkas (konsisten dengan pola compose_conversation)
panel_to_card = _panel_to_card
