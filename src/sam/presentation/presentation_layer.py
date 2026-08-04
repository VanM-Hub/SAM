"""Sprint 276 - Presentation Layer: runtime utama (composition-only).

Class service (bukan DTO); setelah konstruksi read-only, tidak menyimpan
state mutabel, tidak melakukan IO/eksekusi. Semua eksekusi nyata tetap
melalui RuntimeService + Approval Gate (di luar scope desktop).
"""
from __future__ import annotations

from typing import Dict, Optional

from sam.runtime_service import RuntimeService

from .dashboard.dashboard_snapshot import DashboardSnapshot
from .foundation import (
    PresentationContract,
)
from .panels import PanelsRegistry
from .panels.panels_registry import default_panels
from .workspace import WorkspaceModel
from .commands.presentation_controller import PresentationController
from .composition.presentation_pipeline import PresentationPipeline
from .viewmodels.presentation_summary import PresentationSummary


class PresentationLayer:
    """Presentation Layer: mengomposisikan workspace + panels + dashboard.

    Pipeline: foundation -> workspace -> panels -> dashboard -> runtime.
    Semua artefak immutable & deterministik; tanpa IO/network/thread.

    Session 04 (AD-S04): menerima RuntimeService VIA dependency injection dari
    entry (Desktop). Presentation HANYA membaca kontrak RuntimeService
    (lifecycle/readiness/status/descriptor/metadata/contract) sebagai snapshot
    immutable. TIDAK membuat RuntimeService, TIDAK tahu RuntimeCoordinator /
    ExecutionRuntime, TIDAK business logic.
    """

    def __init__(
        self,
        model: Optional[WorkspaceModel] = None,
        registry: Optional[PanelsRegistry] = None,
        contract: Optional[PresentationContract] = None,
        runtime_service: Optional[RuntimeService] = None,
    ):
        self._model = model or WorkspaceModel()
        self._registry = registry or PanelsRegistry().register_all(default_panels())
        self._contract = contract or PresentationContract()
        self._runtime_service = runtime_service
        self._locked = True

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False):
            raise AttributeError(f"PresentationLayer is immutable: {name}")
        super().__setattr__(name, value)

    @property
    def model(self) -> WorkspaceModel:
        return self._model

    @property
    def registry(self) -> PanelsRegistry:
        return self._registry

    @property
    def contract(self) -> PresentationContract:
        return self._contract

    @property
    def runtime_service(self) -> Optional[RuntimeService]:
        """RuntimeService yang di-inject (atau None bila tidak di-DI)."""
        return self._runtime_service

    @property
    def has_runtime_service(self) -> bool:
        """Apakah presentation menerima RuntimeService via DI."""
        return self._runtime_service is not None

    def runtime_status(self) -> Dict[str, object]:
        """Runtime Status dari kontrak RuntimeService (bukan internal coordinator).

        Hanya membaca: lifecycle (status_dict), descriptor, metadata, contract.
        Immutable & deterministic; TIDAK menyentuh RuntimeCoordinator / ExecutionRuntime.
        Bila tidak ada service yang di-inject, kembalikan snapshot kosong.
        """
        if self._runtime_service is None:
            return {
                "available": False,
                "status": "not_injected",
                "initialized": False,
            }
        svc = self._runtime_service
        lifecycle = svc.status_dict()
        descriptor = svc.descriptor.as_dict()
        metadata = svc.metadata.as_dict()
        contract = svc.contract.as_dict()
        return {
            "available": True,
            "name": svc.name,
            "status": lifecycle.get("status"),
            "initialized": lifecycle.get("initialized", False),
            "started": lifecycle.get("started", False),
            "lifecycle": lifecycle,
            "descriptor": descriptor,
            "metadata": metadata,
            "contract": contract,
        }

    def run(self) -> DashboardSnapshot:
        """Jalankan pipeline desktop: komposisi, bukan eksekusi."""
        issues = PresentationController.validate(self._model)
        if issues:
            raise ValueError(f"Workspace invalid: {issues}")
        dash = PresentationController.compose_dashboard(self._registry)
        return dash.run()

    def snapshot_summary(self) -> PresentationSummary:
        return PresentationSummary(
            panels=self._registry.names,
            dashboard_cards=len(self._registry),
        )

    def pipeline_stages(self) -> tuple:
        return PresentationPipeline().stages

    def as_dict(self) -> dict:
        return {
            "model": self._model.as_dict(),
            "panels": self._registry.names,
            "contract": self._contract.as_dict(),
            "preview_only": True,
            "execute_self": False,
        }
