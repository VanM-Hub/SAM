"""ENG-H-001 (AP-MISSION-003-001) — H10 Dashboard Integration.

Program H — Dashboard. Mengintegrasikan panel Dashboard yang telah ter-wire
ke jalur resmi runtime_service menjadi satu alur tampilan sederhana.
Service composition-only: menggabungkan hasil dari wiring (yang memanggil
jalur runtime_service.api) — TANPA bypass, TANPA akses langsung Runtime/
Provider/Connector/Registry/ExecutionRuntime, TANPA business logic eksekusi.

Sesuai Activation Matrix Program H:
  - workflow / execution / audit / runtime / health  : jalur resmi (ready).
  - approval : HANYA memvisualisasikan status `approved` dari outcome
    preview (limited) — TIDAK membuat Approval view/runtime/gateway/preview/api.
  - mission / provider / connector / telemetry : missing -> dilaporkan
    'escalated' (tidak dijalankan, tidak memalsukan result).

Desain composition (pola Program G G10):
  - wiring memegang handler yang memanggil gateway runtime_service (injected).
  - consumers diterima via dependency injection (sama seperti gateway).
  - presentation TIDAK membuat resolver/builder; tanpa consumer di-inject,
    capability dilaporkan 'unwired' dan tidak dipanggil.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .viewmodel import DashboardViewModel
from .wiring import DashboardRuntimeWiring

__all__ = ["DashboardResult", "DashboardIntegration"]


@dataclass(frozen=True)
class DashboardResult:
    """Hasil terintegrasi satu tampilan Dashboard (immutable, composition)."""

    dashboard_id: str = "main"
    panels: dict = field(default_factory=dict)          # area -> result dict
    panel_status: Dict[str, str] = field(default_factory=dict)
    approval: Optional[dict] = None                     # visualisasi state (limited)
    escalated: Dict[str, str] = field(default_factory=dict)  # area missing

    def approval_status(self) -> str:
        if not self.approval:
            return "unknown"
        return "approved" if self.approval.get("approved") else "pending"

    def as_dict(self) -> dict:
        return {
            "dashboard_id": self.dashboard_id,
            "panels": dict(self.panels),
            "panel_status": dict(self.panel_status),
            "approval": self.approval,
            "escalated": dict(self.escalated),
        }


class DashboardIntegration:
    """Integrasi dashboard — menggabungkan hasil wiring (composition-only)."""

    AREAS = ("workflow", "execution", "audit", "runtime", "health")
    ESCALATED_AREAS = ("mission", "provider", "connector", "telemetry")
    # approval diwakili dari field `approved` outcome execution (limited).

    def __init__(
        self,
        viewmodel: DashboardViewModel,
        wiring: DashboardRuntimeWiring,
    ) -> None:
        self._viewmodel = viewmodel
        self._wiring = wiring

    def run(self, context=None, execution_id: str = "h1_exec") -> DashboardResult:
        """Susun tampilan Dashboard terintegrasi (preview, no-execute).

        Menjalankan handler jalur resmi per area. Executor context
        dievaluasi per area melalui handler (composition); context yang
        tidak diperlukan (runtime/health) menerima None.
        """
        panels: Dict[str, Any] = {}
        status: Dict[str, str] = {}

        for area in self.AREAS:
            handler = self._wiring._handlers.get(area)
            if handler is None:
                status[area] = "unwired"
                continue
            try:
                if area in ("runtime", "health"):
                    result = handler()
                elif area == "execution":
                    result = handler(context, execution_id)
                elif area == "workflow":
                    result = handler(context, f"{area}_1", execution_id)
                elif area == "audit":
                    result = handler(context, f"{area}_1", execution_id)
                else:  # pragma: no cover — safety
                    result = handler(context, f"{area}_1", execution_id)
                panels[area] = result
                status[area] = "ok"
            except Exception as exc:  # noqa: BLE001 — composition boundary
                panels[area] = {"error": type(exc).__name__}
                status[area] = f"error: {type(exc).__name__}"

        # --- Approval: visualisasi state dari outcome execution (limited) ---
        approval = None
        execution = panels.get("execution")
        if isinstance(execution, dict) and "approved" in execution:
            approval = {"approved": bool(execution.get("approved", False))}
        elif isinstance(execution, dict) and "execution" in execution:
            inner = execution["execution"]
            if isinstance(inner, dict):
                approval = {"approved": bool(inner.get("approved", False))}

        escalated = {a: "missing" for a in self.ESCALATED_AREAS}

        return DashboardResult(
            dashboard_id=self._viewmodel.dashboard_id,
            panels=panels,
            panel_status=status,
            approval=approval,
            escalated=escalated,
        )
