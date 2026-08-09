"""Connector Registry & Lifecycle - WP-12/WP-13 (MISSION-5.2 / IP-5.2-002).

Registry + lifecycle connector. Connector tidak melakukan automatic invocation
atau implicit execution.
"""
from __future__ import annotations

from typing import Optional, Tuple

from .connector_model import ConnectorHandle, ConnectorState, ToolConnector


class ConnectorRegistry:
    """Registry Connector (read/discovery, bukan execution)."""

    def __init__(self) -> None:
        self._connectors: dict = {}

    def register(self, connector: ToolConnector) -> None:
        self._connectors[connector.handle.connector_id] = connector

    def get(self, connector_id: str) -> Optional[ToolConnector]:
        return self._connectors.get(connector_id)

    def by_tool(self, tool_id: str) -> Tuple[ToolConnector, ...]:
        return tuple(c for c in self._connectors.values() if c.handle.tool_id == tool_id)

    def list(self) -> Tuple[ToolConnector, ...]:
        return tuple(self._connectors.values())

    def connected(self) -> Tuple[ToolConnector, ...]:
        return tuple(c for c in self._connectors.values() if c.connected)

    def size(self) -> int:
        return len(self._connectors)


def _updated(handle: ConnectorHandle, state: ConnectorState) -> ConnectorHandle:
    return ConnectorHandle(
        connector_id=handle.connector_id,
        tool_id=handle.tool_id,
        connector_type=handle.connector_type,
        endpoint=handle.endpoint,
        state=state,
        created_at=handle.created_at,
        metadata=handle.metadata,
    )


class ConnectorLifecycle:
    """Mengelola state lifecycle connector."""

    def __init__(self) -> None:
        self._connectors: dict = {}

    def track(self, connector: ToolConnector) -> None:
        self._connectors[connector.handle.connector_id] = connector

    def connect(self, connector_id: str) -> Optional[ConnectorHandle]:
        connector = self._connectors.get(connector_id)
        if connector is None:
            return None
        connector.handle = _updated(connector.handle, ConnectorState.CONNECTED)
        return connector.handle

    def disconnect(self, connector_id: str) -> Optional[ConnectorHandle]:
        connector = self._connectors.get(connector_id)
        if connector is None:
            return None
        connector.handle = _updated(connector.handle, ConnectorState.DISCONNECTED)
        return connector.handle

    def error(self, connector_id: str) -> Optional[ConnectorHandle]:
        connector = self._connectors.get(connector_id)
        if connector is None:
            return None
        connector.handle = _updated(connector.handle, ConnectorState.ERROR)
        return connector.handle

    def state_of(self, connector_id: str) -> Optional[ConnectorState]:
        connector = self._connectors.get(connector_id)
        return connector.handle.state if connector else None
