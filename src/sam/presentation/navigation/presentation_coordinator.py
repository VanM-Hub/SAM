"""Sprint 276 - Presentation Layer: coordinator (service, tanpa IO)."""
from __future__ import annotations

from typing import Tuple

from ..conversation.bridge import ConversationBridge
from ..dashboard_bridge.bridge import DashboardBridge
from ..workspace.workspace_state import WorkspaceState
from ..commands.presentation_controller import PresentationController


class PresentationCoordinator:
    """Koordinasi bridge + controller secara deterministik (tanpa IO)."""

    @staticmethod
    def modes(
        conversation: ConversationBridge,
        dashboard: DashboardBridge,
    ) -> Tuple[str, ...]:
        return (
            tuple(conversation.scope())
            + tuple(dashboard.scope())
        )

    @staticmethod
    def assemble(
        state: WorkspaceState,
        controller: PresentationController,
        *panels: str,
    ) -> WorkspaceState:
        visible = tuple(dict.fromkeys(state.visible + panels))
        return WorkspaceState(
            docked=state.docked,
            floating=state.floating,
            visible=visible,
            dirty=state.dirty,
        )

    @staticmethod
    def ready_conversation(conversation: ConversationBridge) -> bool:
        return conversation.read_only()

    @staticmethod
    def ready_dashboard(dashboard: DashboardBridge) -> bool:
        return dashboard.read_only()
