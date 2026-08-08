# Layout Model - IP-3.5-001 (AO-ENG-001, MISSION-3.5)
# WP-05: model deklaratif tata letak workspace & panels.
#
# Bound context: src/sam/platform/ (consumer-only).
# Guardrail: Layout != Execution; Tata letak != Otoritas;
#   Deklarasi panels != Control runtime.

"""Layout Model.

Mendeskripsikan struktur tata letak workspace: region, panel, dan area
tampilan, semuanya deklaratif. Layout hanya mengatur PENYAJIAN, tidak pernah
mengeksekusi atau mengontrol capability.
"""

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class PanelSlot:
    """Sebuah slot panel dalam satu region layout.

    Deklaratif: menunjuk apa yang TAMPIL di slot, bukan apa yang dijalankan.
    """

    slot_id: str
    region: str
    perspective: str = ""
    # Domain view yang ditampilkan di slot ini (deklaratif).
    domain: str = ""
    # Prioritas tampilan (lebih besar = lebih utama; deterministik).
    priority: int = 0

    def __post_init__(self) -> None:
        if not self.slot_id or not self.slot_id.strip():
            raise ValueError("slot_id wajib diisi.")


@dataclass(frozen=True)
class LayoutModel:
    """Model tata letak workspace.

    Terdiri dari region (mis. header, main, aside, footer) dan panel slots.
    Urutan slots per region deterministik (berdasarkan priority desc, lalu id).
    """

    layout_id: str
    regions: Tuple[str, ...] = ()
    panels: Tuple[PanelSlot, ...] = ()

    def __post_init__(self) -> None:
        if not self.layout_id or not self.layout_id.strip():
            raise ValueError("layout_id wajib diisi.")

    def panels_in(self, region: str) -> Tuple[PanelSlot, ...]:
        """Panel slots dalam region, urutan deterministik (priority desc, id)."""
        return tuple(
            sorted(
                (p for p in self.panels if p.region == region),
                key=lambda p: (-p.priority, p.slot_id),
            )
        )

    def region_order(self) -> Tuple[str, ...]:
        """Urutan region (deterministik)."""
        return tuple(sorted(self.regions))
