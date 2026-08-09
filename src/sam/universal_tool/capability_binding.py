"""Capability Binding - WP-16 (MISSION-5.2 / IP-5.2-002).

Menghubungkan capability connector dengan capability model Tool.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .tool_descriptor import ToolCapabilityKind


@dataclass(frozen=True)
class CapabilityBinding:
    """Ikatan capability yang didukung sebuah connector."""

    connector_id: str
    capabilities: Tuple[ToolCapabilityKind, ...] = ()

    def supports(self, kind: ToolCapabilityKind) -> bool:
        return kind in self.capabilities

    def as_dict(self) -> dict:
        return {
            "connector_id": self.connector_id,
            "capabilities": [k.value for k in self.capabilities],
        }


class CapabilityBinder:
    """Mengelola mapping connector -> capability."""

    def __init__(self) -> None:
        self._map: dict = {}

    def bind(self, connector_id: str, capabilities: Tuple[ToolCapabilityKind, ...]) -> CapabilityBinding:
        binding = CapabilityBinding(connector_id=connector_id, capabilities=capabilities)
        self._map[connector_id] = binding
        return binding

    def binding_for(self, connector_id: str) -> CapabilityBinding:
        return self._map.get(connector_id, CapabilityBinding(connector_id=connector_id))

    def connectors_for(self, kind: ToolCapabilityKind) -> Tuple[str, ...]:
        return tuple(cid for cid, b in self._map.items() if b.supports(kind))
