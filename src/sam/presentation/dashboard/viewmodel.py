"""ENG-H-001 (AP-MISSION-003-001) — G1 Dashboard Structure: ViewModel.

Program H — Dashboard. Presentation Capability (read-only). ViewModel
hanya menyusun state tampilan Dashboard; TIDAK memuat business logic,
TIDAK memanggil Runtime/Registry/Provider/Connector/ExecutionRuntime.
Konsisten dengan pola Program G (G1 structure) serta Composition Principle
(Art. XVI) dan pola Sprint 276 (service composition-only + DTO immutable).

Status activation per area mengikuti Dashboard Activation Matrix
(scope Program H): area ✅ Ready akan diisi hasil runtime_service (G2+),
area ⚠️ Partial hanya divisualisasikan dari outcome preview, area ✗ Missing
diekskalasi (tidak diimplementasikan sebagai jalur baru).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class DashboardPanel:
    """Satu area Dashboard (deklaratif, read-only).

    Mewakili area yang divisualisasikan + status activation path-nya:
    - status "ready"      -> area punya activation path resmi (Implement).
    - status "limited"    -> hanya visualisasi state (Approval, dari outcome).
    - status "missing"    -> tidak ada activation path (Escalation, bukan jalur).
    - status "detached"   -> placeholder sebelum wiring (belum terpasang).
    """

    area: str
    status: str = "detached"
    source: str = "runtime_service.api"
    sections: Tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "area": self.area,
            "status": self.status,
            "source": self.source,
            "sections": list(self.sections),
        }


@dataclass(frozen=True)
class DashboardViewModel:
    """State tampilan Dashboard (komposisi, read-only).

    G1: struktur awal — capability belum dicolok (diisi G2+ lewat jalur
    runtime_service). Field `panels` mencerminkan area Dashboard pada
    Activation Matrix Program H sebagai placeholder.
    """

    dashboard_id: str = "main"
    mode: str = "capability"
    read_only: bool = True
    panels: Tuple[DashboardPanel, ...] = field(
        default_factory=lambda: (
            DashboardPanel(area="workflow", status="detached", sections=("status",)),
            DashboardPanel(area="execution", status="detached", sections=("preview", "approval")),
            DashboardPanel(area="audit", status="detached", sections=("entries",)),
            DashboardPanel(area="runtime", status="detached", sections=("status",)),
            DashboardPanel(area="health", status="detached", sections=("healthy",)),
            DashboardPanel(area="approval", status="detached", sections=("approved",)),
            DashboardPanel(area="mission", status="missing", sections=()),
            DashboardPanel(area="provider", status="missing", sections=()),
            DashboardPanel(area="connector", status="missing", sections=()),
            DashboardPanel(area="telemetry", status="missing", sections=()),
        )
    )

    def panel(self, area: str) -> DashboardPanel | None:
        """Akses panel per area (read-only accessor; bukan eksekusi)."""
        for p in self.panels:
            if p.area == area:
                return p
        return None

    def panel_status(self, area: str) -> str:
        p = self.panel(area)
        return p.status if p is not None else "unknown"

    def as_dict(self) -> dict:
        return {
            "dashboard_id": self.dashboard_id,
            "mode": self.mode,
            "read_only": self.read_only,
            "panels": [p.as_dict() for p in self.panels],
        }

    def panel_list(self) -> Tuple[str, ...]:
        return tuple(p.area for p in self.panels)
