"""Tool API - WP-08 (MISSION-5.2 / IP-5.2-001).

API publik untuk mengakses seluruh capability foundation Tool. Tetap pada
bounded context; tidak mengambil alih Governance atau Execution.
"""
from __future__ import annotations

from typing import Optional, Tuple

from .tool_descriptor import ToolCapabilityKind, ToolDescriptor
from .tool_discovery import ToolDiscovery, ToolDiscoveryResult
from .tool_health import ToolHealth, ToolHealthCheck
from .tool_identity import ToolIdentity, ToolStatus
from .tool_registry import ToolRegistry


class ToolAPI:
    """API publik bounded context Universal Tool Foundation."""

    def __init__(
        self,
        registry: Optional[ToolRegistry] = None,
        discovery: Optional[ToolDiscovery] = None,
        health: Optional[ToolHealthCheck] = None,
    ) -> None:
        self.registry = registry or ToolRegistry()
        self.discovery = discovery or ToolDiscovery(self.registry)
        self._healthcheck = health or ToolHealthCheck()

    def register(self, identity: ToolIdentity, availability: bool = False):
        return self.registry.register(identity, availability=availability)

    def lookup(self, tool_id: str) -> Optional[ToolIdentity]:
        return self.registry.lookup(tool_id)

    def list_tools(self, status: Optional[ToolStatus] = None) -> Tuple[ToolIdentity, ...]:
        return self.registry.list(status=status)

    def discover(self, kind: Optional[ToolCapabilityKind] = None) -> Tuple[ToolDiscoveryResult, ...]:
        if kind is None:
            return tuple(ToolDiscoveryResult(tool_id=p.tool_id) for p in self.registry.list())
        return self.discovery.discover_by_capability(kind)

    def discover_descriptors(self) -> Tuple[ToolDescriptor, ...]:
        return self.discovery.discover_descriptors()

    def set_descriptors(self, descriptors: Tuple[ToolDescriptor, ...]) -> None:
        self.discovery.set_descriptors(descriptors)

    def health(self, tool_id: str) -> Optional[ToolHealth]:
        if self.registry.lookup(tool_id) is None:
            return None
        return self._healthcheck.assess(tool_id)
