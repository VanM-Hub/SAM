"""OpenClaw Gateway — gerbang ke OpenClaw Runtime (Sprint 235).

Menghubungkan ProviderIntegration (Program A) dengan pola OpenClaw Runtime
tanpa mengubah legacy subsystem (src/sam/openclaw/). Gateway ini hanya
menyediakan request tool berformat OpenClaw untuk preview; TIDAK invoke.
Preview-only, external_calls=0, immutable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from .runtime_integration import ProviderIntegration


@dataclass(frozen=True)
class OpenClawGatewayToolRequest:
    """Request tool OpenClaw (immutable, preview-only)."""
    tool: str
    arguments: Dict[str, Any] = field(default_factory=dict)
    runtime_id: str = "openclaw-runtime-v1"
    preview: bool = True
    invoked: bool = False
    external_calls: int = 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "arguments": dict(self.arguments),
            "runtime_id": self.runtime_id,
            "preview": self.preview,
            "invoked": self.invoked,
            "external_calls": self.external_calls,
        }


class OpenClawGateway:
    """Gerbang preview ke OpenClaw tanpa invoke tools."""

    def __init__(self, integration: "ProviderIntegration | None" = None) -> None:
        self._integration = integration or ProviderIntegration()

    def attach(self, integration: ProviderIntegration) -> None:
        self._integration = integration

    def request_tool(
        self, tool: str, arguments: Dict[str, Any] | None = None
    ) -> OpenClawGatewayToolRequest:
        """Bangun request tool OpenClaw (preview, tidak invoke)."""
        args = arguments or {}
        # Tidak ada provider-specific logic; hanya membungkus request.
        return OpenClawGatewayToolRequest(
            tool=tool,
            arguments=dict(args),
            runtime_id="openclaw-runtime-v1",
            preview=True,
            invoked=False,
            external_calls=0,
        )

    def available_providers(self) -> Tuple[str, ...]:
        return tuple(self._integration.list_providers())

    def count_providers(self) -> int:
        return self._integration.count()

    def is_ready(self) -> bool:
        return self._integration.count() > 0
