"""Sprint 275 + ENG-H-001 (G1) - Desktop Dashboard: Presentation Capability.

Modul deklaratif lama (Sprint 275) dipertahankan untuk snapshot read-only.
Struktur H1 (Program H) menambah ViewModel dan UI Composition sebagai fondasi
Presentation Capability (module/ViewModel/UI composition). Capability
dihubungkan ke RuntimeService pada H2+ (via jalur runtime_service.api yang
sudah ada); di sini TIDAK ada business logic dan TIDAK ada akses langsung ke
Runtime/Registry/Provider/Connector.
"""
from .card_model import DashboardCard
from .dashboard_composer import DashboardComposer
from .dashboard_layout import DashboardLayout
from .dashboard_runtime import DashboardRuntime
from .dashboard_snapshot import DashboardSnapshot
from .viewmodel import DashboardPanel, DashboardViewModel
from .composition import DashboardComposition, compose_dashboard, panel_to_card
from .wiring import DashboardRuntimeWiring, wire_dashboard_runtime
from .integration import DashboardResult, DashboardIntegration

__all__ = [
    "DashboardCard",
    "DashboardComposer",
    "DashboardLayout",
    "DashboardRuntime",
    "DashboardSnapshot",
    "DashboardPanel",
    "DashboardViewModel",
    "DashboardComposition",
    "compose_dashboard",
    "panel_to_card",
    "DashboardRuntimeWiring",
    "wire_dashboard_runtime",
    "DashboardResult",
    "DashboardIntegration",
]
