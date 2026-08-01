"""Sprint 272 - Presentation Layer Foundation: capability."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PresentationCapability:
    """Kapabilitas yang dimiliki Presentation Layer (composition-only)."""

    visualize: bool = True
    compose_workspace: bool = True
    present_panels: bool = True
    render_dashboard: bool = True
    monitor: bool = True
    certify: bool = True
    execute_self: bool = False
    supported_modes: Tuple[str, ...] = (
        "foundation",
        "workspace",
        "panels",
        "dashboard",
        "runtime",
        "monitoring",
        "certification",
        "integration",
    )

    def as_dict(self) -> dict:
        return {
            "visualize": self.visualize,
            "compose_workspace": self.compose_workspace,
            "present_panels": self.present_panels,
            "render_dashboard": self.render_dashboard,
            "monitor": self.monitor,
            "certify": self.certify,
            "execute_self": self.execute_self,
            "supported_modes": list(self.supported_modes),
        }
