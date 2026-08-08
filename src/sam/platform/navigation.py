# Workspace Navigation - IP-3.5-001 (AO-ENG-001, MISSION-3.5)
# WP-02: struktur navigasi workspace agar operator menjelajah seluruh domain
#        capability view secara konsisten.
#
# Bound context: src/sam/platform/ (consumer-only).
# Guardrail: Navigasi != Eksekusi; Arahkan tampilan != Jalankan capability;
#   Navigation model != Control plane.

"""Workspace Navigation.

Model navigasi workspace: lintasan (route) antar domain & perspective agar
operator dapat menjelajah seluruh capability view. Navigasi MURNI tentang
pergerakan TAMPILAN, tidak pernah mengeksekusi capability atau mengendalikan
runtime.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class NavigationRoute:
    """Sebuah rute navigasi deklaratif dalam workspace.

    Rute menyediakan tujuan tampilan, bukan instruksi eksekusi.
    """

    route_id: str
    domain: str = ""
    perspective: str = ""
    label: str = ""
    parent: str = ""

    def __post_init__(self) -> None:
        if not self.route_id or not self.route_id.strip():
            raise ValueError("route_id wajib diisi.")


@dataclass(frozen=True)
class NavigationModel:
    """Model navigasi workspace.

    Himpunan rute; mencarikan rute berdasarkan domain/perspective secara
    deterministik.
    """

    routes: Tuple[NavigationRoute, ...] = ()

    def route(self, route_id: str) -> Optional[NavigationRoute]:
        for r in self.routes:
            if r.route_id == route_id:
                return r
        return None

    def routes_for_domain(self, domain: str) -> Tuple[NavigationRoute, ...]:
        """Rute yang menunjuk ke domain (urutan sort)."""
        return tuple(sorted((r for r in self.routes if r.domain == domain),
                           key=lambda r: r.route_id))

    def children_of(self, route_id: str) -> Tuple[NavigationRoute, ...]:
        """Rute yang memiliki <route_id> sebagai parent (urut)."""
        return tuple(sorted((r for r in self.routes if r.parent == route_id),
                            key=lambda r: r.route_id))

    def route_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(r.route_id for r in self.routes))


def build_navigation(routes: Tuple[NavigationRoute, ...]) -> NavigationModel:
    """Bangun NavigationModel dari rute; validasi parent referensi valid.

    Rute dengan parent yang tidak dikenal tetap boleh (parent opsional),
    tapi parent yang menunjuk ke rute None tidak dianggap error; hanya
    mengakibatkan rute itu menjadi "root" (tidak punya parent valid).
    """
    model = NavigationModel(routes=routes)
    return model
