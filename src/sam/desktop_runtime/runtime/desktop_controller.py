"""Sprint 276 - Desktop Runtime: controller (service, composition-only)."""
from __future__ import annotations

from typing import List, Tuple

from ..dashboard import DashboardRuntime
from ..dashboard.card_model import DashboardCard
from ..panels.panels_registry import PanelsRegistry
from ..workspace.workspace_model import WorkspaceModel
from ..workspace.workspace_session import WorkspaceSession
from ..workspace.workspace_validator import WorkspaceValidator


class DesktopController:
    """Controller desktop: menyusun model, registry, dan session.

    Class service (bukan DTO); tidak menyimpan state mutabel.
    """

    @staticmethod
    def build_session(model: WorkspaceModel) -> WorkspaceSession:
        return WorkspaceSession(model=model, panels=model.panels)

    @staticmethod
    def validate(model: WorkspaceModel) -> List[str]:
        return WorkspaceValidator.validate_model(model)

    @staticmethod
    def compose_dashboard(registry: PanelsRegistry) -> DashboardRuntime:
        """Komposisi panel -> kartu dashboard (read-only, tanpa eksekusi)."""
        cards = tuple(
            DashboardCard(title=p.name, source_runtime=p.source_runtime)
            for p in registry.panels
        )
        return DashboardRuntime(cards=cards)

    @staticmethod
    def panel_titles(registry: PanelsRegistry) -> Tuple[str, ...]:
        return registry.names
