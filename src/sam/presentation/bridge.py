"""Sprint 272 - Presentation Layer Foundation: PresentationLayerBridge (read-only).

Menggabungkan Conversation Bridge + Dashboard Bridge menjadi satu titik
komposisi untuk Presentation Layer. Hanya membaca metadata secara statis,
tidak memanggil subsystem lain.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .conversation.bridge import ConversationBridge
from .dashboard_bridge.bridge import DashboardBridge


@dataclass(frozen=True)
class PresentationLayerBridge:
    """Bridge read-only yang menyatukan conversation & dashboard desktop."""

    conversation: ConversationBridge = field(
        default_factory=ConversationBridge
    )
    dashboard: DashboardBridge = field(default_factory=DashboardBridge)

    def read_only(self) -> bool:
        return True

    def modes(self) -> Tuple[str, ...]:
        return (
            tuple(self.conversation.scope())
            + tuple(self.dashboard.scope())
        )

    def as_dict(self) -> dict:
        return {
            "read_only": True,
            "conversation": self.conversation.as_dict(),
            "dashboard": self.dashboard.as_dict(),
        }
