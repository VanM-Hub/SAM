"""ENG-H-001 (AP-MISSION-003-001) — G2 Dashboard: RuntimeService wiring.

Program H — Dashboard. Menghubungkan Dashboard (presentation) ke jalur
resmi runtime_service. Gateway `ConversationPreviewGateway` DITERIMA via
dependency injection dari entry/web — presentation TIDAK membuat gateway,
TIDAK membangun RuntimeAPI, TIDAK mengakses Runtime/Provider/Connector/
Registry/ExecutionRuntime secara langsung. Runtime status & health diakses
melalui jalur resmi `gateway.api.status()` / `gateway.api.health()`
(RuntimeAPI kontrak) — bukan import langsung ke runtime manapun.

Alur (sesuai Activation Matrix Program H):
    Presentation -> Dashboard -> runtime_service(ConversationPreviewGateway)
    -> RuntimeService (single entry) -> Existing Runtime Citizens (preview).

Status per area:
  - ready   -> handler terpasang ke jalur resmi (workflow/execution/audit/runtime/health)
  - limited -> Approval: HANYA membaca status `approved` dari outcome preview
               (visualisasi state, TIDAK membuat Approval view/runtime/gateway/preview/api)
  - missing -> Mission/Provider/Connector/Telemetry: tidak ada activation path
               (escalation; handler TIDAK dipanggil, hanya status 'missing')
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

# Satu-satunya dependency keluar: package runtime_service (diizinkan Arch Package).
from sam.runtime_service.api import ConversationPreviewGateway

from .viewmodel import DashboardPanel, DashboardViewModel

__all__ = ["DashboardRuntimeWiring", "wire_dashboard_runtime"]


class DashboardRuntimeWiring:
    """Wiring Dashboard -> gateway runtime_service (injected). Read-only.

    'consumers' (workflow/audit resolver) di-inject dari entry/web seperti
    pola Program G. Presentation hanya menyusun handler; tidak membuat
    resolver dan tidak mengeksekusi runtime.
    """

    # Area dengan activation path resmi -> handler terpasang.
    READY_AREAS = ("workflow", "execution", "audit", "runtime", "health")
    # Area limited: Approval -> hanya visualisasi state dari outcome preview.
    LIMITED_AREAS = ("approval",)
    # Area missing -> escalation, tidak ada jalur resmi.
    MISSING_AREAS = ("mission", "provider", "connector", "telemetry")

    def __init__(
        self,
        gateway: ConversationPreviewGateway,
        viewmodel: DashboardViewModel,
        consumers: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._gateway = gateway
        self._viewmodel = viewmodel
        self._consumers = consumers or {}
        self._handlers: Dict[str, Callable[..., Any]] = {}
        self._attach_all()

    def _attach_all(self) -> None:
        for area in self.READY_AREAS:
            handler = getattr(self, f"_handle_{area}", None)
            if handler is not None:
                self._handlers[area] = handler
        # Approval: visualisasi state (bukan jalur approval terpisah).

    # --- handler area READY (jalur resmi runtime_service) ---

    def _handle_workflow(
        self, context, workflow_id: str, execution_id: str, knowledge_id: str = ""
    ) -> dict:
        consumer = self._consumers.get("workflow")
        knowledge_consumer = self._consumers.get("knowledge")
        return self._gateway.preview_with_workflow(
            context, consumer, workflow_id, execution_id, knowledge_consumer, knowledge_id
        )

    def _handle_execution(self, context, execution_id: str) -> dict:
        return self._gateway.preview(context, execution_id=execution_id).as_dict()

    def _handle_audit(self, context, audit_id: str, execution_id: str) -> dict:
        consumer = self._consumers.get("audit")
        return self._gateway.preview_with_audit(context, consumer, audit_id, execution_id)

    def _handle_runtime(self) -> dict:
        # Jalur resmi: RuntimeAPI.status() (kontrak runtime_service.api).
        return self._gateway.api.status().as_dict()

    def _handle_health(self) -> dict:
        return self._gateway.api.health().as_dict()

    # --- status per area ---

    def status_map(self) -> dict:
        """Status activation per area Dashboard (mengikuti Activation Matrix)."""
        status = {a: "ready" for a in self.READY_AREAS}
        for a in self.LIMITED_AREAS:
            status[a] = "limited"
        for a in self.MISSING_AREAS:
            status[a] = "missing"
        return status

    @property
    def gateway(self) -> ConversationPreviewGateway:
        return self._gateway

    def has_handler(self, area: str) -> bool:
        return area in self._handlers

    def area_status(self, area: str) -> str:
        return self.status_map().get(area, "unknown")

    def as_dict(self) -> dict:
        return {
            "wired": True,
            "via": "runtime_service.api.ConversationPreviewGateway",
            "status": self.status_map(),
            "handlers": {a: self.has_handler(a) for a in self.READY_AREAS},
        }


def wire_dashboard_runtime(
    gateway: ConversationPreviewGateway,
    viewmodel: Optional[DashboardViewModel] = None,
    consumers: Optional[Dict[str, Any]] = None,
) -> DashboardRuntimeWiring:
    """Wire Dashboard ke gateway (dependency injection dari entry)."""
    if viewmodel is None:
        viewmodel = DashboardViewModel()
    return DashboardRuntimeWiring(gateway, viewmodel, consumers)
