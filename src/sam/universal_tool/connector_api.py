"""Connector API - WP-18 (MISSION-5.2 / IP-5.2-002).

API publik framework Connector. Tidak melakukan invocation otomatis dan tidak
melewati Governance/Execution boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .connector_health import ConnectorHealth, ConnectorHealthCheck
from .connector_lifecycle import ConnectorLifecycle, ConnectorState
from .connector_model import ConnectorHandle, ConnectorType, ToolConnector
from .connector_registry import ConnectorRegistry
from .connection_management import ConnectionManager


@dataclass(frozen=True)
class ConnectorView:
    """Tampilan connector (handle + status)."""

    handle: ConnectorHandle
    state: ConnectorState

    def as_dict(self) -> dict:
        return {"handle": self.handle.as_dict(), "state": self.state.value}


class ConnectorAPI:
    """API publik Connector Framework."""

    def __init__(
        self,
        registry: Optional[ConnectorRegistry] = None,
        lifecycle: Optional[ConnectorLifecycle] = None,
        connections: Optional[ConnectionManager] = None,
        health: Optional[ConnectorHealthCheck] = None,
    ) -> None:
        self.registry = registry or ConnectorRegistry()
        self.lifecycle = lifecycle or ConnectorLifecycle()
        self.connections = connections or ConnectionManager()
        self._healthcheck = health or ConnectorHealthCheck()

    def register(self, connector: ToolConnector) -> None:
        self.registry.register(connector)
        self.lifecycle.track(connector)

    def connect(self, connector_id: str) -> Optional[ConnectorHandle]:
        handle = self.lifecycle.connect(connector_id)
        if handle is not None:
            self.connections.connect(connector_id)
        return handle

    def disconnect(self, connector_id: str) -> Optional[ConnectorHandle]:
        handle = self.lifecycle.disconnect(connector_id)
        if handle is not None:
            self.connections.disconnect(connector_id)
        return handle

    def view(self, connector_id: str) -> Optional[ConnectorView]:
        connector = self.registry.get(connector_id)
        if connector is None:
            return None
        return ConnectorView(handle=connector.handle, state=connector.handle.state)

    def health(self, connector_id: str) -> Optional[ConnectorHealth]:
        if self.registry.get(connector_id) is None:
            return None
        return self._healthcheck.assess(connector_id)

    def connector_type_available(self, ctype: ConnectorType) -> bool:
        return any(c.handle.connector_type == ctype for c in self.registry.list())
