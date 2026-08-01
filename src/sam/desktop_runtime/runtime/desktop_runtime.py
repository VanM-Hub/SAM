"""Sprint 276 - Desktop Runtime: runtime utama (composition-only).

Class service (bukan DTO); setelah konstruksi read-only, tidak menyimpan
state mutabel, tidak melakukan IO/eksekusi. Semua eksekusi nyata tetap
melalui RuntimeService + Approval Gate (di luar scope desktop).
"""
from __future__ import annotations

from typing import Optional

from ..dashboard.dashboard_snapshot import DashboardSnapshot
from ..foundation import (
    DesktopContract,
)
from ..panels import PanelsRegistry
from ..panels.panels_registry import default_panels
from ..workspace import WorkspaceModel
from .desktop_controller import DesktopController
from .desktop_pipeline import DesktopPipeline
from .desktop_summary import DesktopSummary


class DesktopRuntime:
    """Desktop Runtime: mengomposisikan workspace + panels + dashboard.

    Pipeline: foundation -> workspace -> panels -> dashboard -> runtime.
    Semua artefak immutable & deterministik; tanpa IO/network/thread.
    """

    def __init__(
        self,
        model: Optional[WorkspaceModel] = None,
        registry: Optional[PanelsRegistry] = None,
        contract: Optional[DesktopContract] = None,
    ):
        self._model = model or WorkspaceModel()
        self._registry = registry or PanelsRegistry().register_all(default_panels())
        self._contract = contract or DesktopContract()
        self._locked = True

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False):
            raise AttributeError(f"DesktopRuntime is immutable: {name}")
        super().__setattr__(name, value)

    @property
    def model(self) -> WorkspaceModel:
        return self._model

    @property
    def registry(self) -> PanelsRegistry:
        return self._registry

    @property
    def contract(self) -> DesktopContract:
        return self._contract

    def run(self) -> DashboardSnapshot:
        """Jalankan pipeline desktop: komposisi, bukan eksekusi."""
        issues = DesktopController.validate(self._model)
        if issues:
            raise ValueError(f"Workspace invalid: {issues}")
        dash = DesktopController.compose_dashboard(self._registry)
        return dash.run()

    def snapshot_summary(self) -> DesktopSummary:
        return DesktopSummary(
            panels=self._registry.names,
            dashboard_cards=len(self._registry),
        )

    def pipeline_stages(self) -> tuple:
        return DesktopPipeline().stages

    def as_dict(self) -> dict:
        return {
            "model": self._model.as_dict(),
            "panels": self._registry.names,
            "contract": self._contract.as_dict(),
            "preview_only": True,
            "execute_self": False,
        }
