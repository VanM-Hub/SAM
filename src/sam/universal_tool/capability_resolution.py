"""Tool Capability Resolution - WP-21 (MISSION-5.2 / IP-5.2-003).

Menyelesaikan capability Tool yang diminta oleh consumer menjadi invocation
yang valid terhadap connector. Deterministik.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .capability_binding import CapabilityBinder
from .tool_descriptor import ToolCapabilityKind


@dataclass(frozen=True)
class ToolCapabilityResolution:
    """Hasil resolusi capability tool."""

    tool_id: str
    connector_id: str
    capability: ToolCapabilityKind
    resolved: bool

    def as_dict(self) -> dict:
        return {
            "tool_id": self.tool_id,
            "connector_id": self.connector_id,
            "capability": self.capability.value,
            "resolved": self.resolved,
        }


class ToolCapabilityResolver:
    """Resolver capability tool -> connector."""

    def __init__(self, binder: CapabilityBinder) -> None:
        self._binder = binder
        self._tool_connector: dict = {}

    def bind_tool_connector(self, tool_id: str, connector_id: str) -> None:
        self._tool_connector[tool_id] = connector_id

    def resolve(self, tool_id: str, capability: ToolCapabilityKind) -> Optional[ToolCapabilityResolution]:
        connector_id = self._tool_connector.get(tool_id)
        if connector_id is None:
            return ToolCapabilityResolution(tool_id=tool_id, connector_id="", capability=capability, resolved=False)
        binding = self._binder.binding_for(connector_id)
        resolved = binding.supports(capability)
        return ToolCapabilityResolution(
            tool_id=tool_id, connector_id=connector_id, capability=capability, resolved=resolved
        )
