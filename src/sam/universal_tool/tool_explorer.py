"""Tool Explorer & Capability Explorer - WP-31/WP-32 (MISSION-5.2 / IP-5.2-004).

Menjelajahi Tool yang terhubung dan capability-nya. Presentation-layer,
tidak memiliki business logic execution.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .tool_descriptor import ToolCapabilityKind, ToolDescriptor
from .tool_discovery import ToolDiscovery
from .tool_identity import ToolIdentity
from .tool_registry import ToolRegistry


@dataclass(frozen=True)
class CapabilityInfo:
    """Info satu capability tool."""

    kind: ToolCapabilityKind
    name: str

    def as_dict(self) -> dict:
        return {"kind": self.kind.value, "name": self.name}


@dataclass(frozen=True)
class ToolInfo:
    """Info tool untuk dijelajahi."""

    identity: ToolIdentity
    capabilities: Tuple[CapabilityInfo, ...] = field(default_factory=tuple)
    connector_ids: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "identity": self.identity.as_dict(),
            "capabilities": [c.as_dict() for c in self.capabilities],
            "connector_ids": list(self.connector_ids),
        }


class ToolExplorer:
    """Menjelajahi tool (read-only presentation)."""

    def __init__(self, registry: ToolRegistry, discovery: ToolDiscovery) -> None:
        self._registry = registry
        self._discovery = discovery

    def all(self, descriptors: Tuple[ToolDescriptor, ...] = ()) -> Tuple[ToolInfo, ...]:
        self._discovery.set_descriptors(descriptors) if descriptors else None
        info = []
        for tool in self._registry.list():
            caps = tuple(
                CapabilityInfo(kind=c.kind, name=c.name)
                for c in self._descriptor_for(tool.tool_id, descriptors).capabilities
            )
            info.append(ToolInfo(identity=tool, capabilities=caps))
        return tuple(info)

    def _descriptor_for(self, tool_id: str, descriptors: Tuple[ToolDescriptor, ...]):
        for d in descriptors:
            if d.identity.tool_id == tool_id:
                return d
        from .tool_descriptor import ToolDescriptor

        return ToolDescriptor(identity=self._registry.lookup(tool_id)) if self._registry.lookup(tool_id) else None

    def by_capability(self, kind: ToolCapabilityKind) -> Tuple[ToolInfo, ...]:
        matched = {r.tool_id for r in self._discovery.discover_by_capability(kind)}
        return tuple(
            ToolInfo(identity=t) for t in self._registry.list() if t.tool_id in matched
        )
