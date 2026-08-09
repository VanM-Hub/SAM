"""Tool Discovery - WP-06 (MISSION-5.2 / IP-5.2-001).

Discovery Tool secara deterministik berbasis registry & descriptor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .tool_descriptor import ToolCapabilityKind, ToolDescriptor
from .tool_identity import ToolIdentity, ToolStatus
from .tool_registry import ToolRegistry


@dataclass(frozen=True)
class ToolDiscoveryResult:
    """Hasil discovery satu tool."""

    tool_id: str
    capability: Optional[ToolCapabilityKind] = None

    def as_dict(self) -> dict:
        return {"tool_id": self.tool_id, "capability": self.capability.value if self.capability else None}


class ToolDiscovery:
    """Mesin discovery Tool berbasis registry dan descriptor."""

    def __init__(self, registry: ToolRegistry, descriptors: Tuple[ToolDescriptor, ...] = ()) -> None:
        self._registry = registry
        self._descriptors = {d.identity.tool_id: d for d in descriptors}

    def set_descriptors(self, descriptors: Tuple[ToolDescriptor, ...]) -> None:
        self._descriptors = {d.identity.tool_id: d for d in descriptors}

    def discover_tools(self, status: Optional[ToolStatus] = None) -> Tuple[ToolIdentity, ...]:
        return self._registry.list(status=status)

    def discover_by_capability(self, kind: ToolCapabilityKind) -> Tuple[ToolDiscoveryResult, ...]:
        results = []
        for tool_id, desc in self._descriptors.items():
            if desc.capability(kind) is not None:
                results.append(ToolDiscoveryResult(tool_id=tool_id, capability=kind))
        return tuple(results)

    def discover_descriptors(self) -> Tuple[ToolDescriptor, ...]:
        return tuple(self._descriptors.values())
