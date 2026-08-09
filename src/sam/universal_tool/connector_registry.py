"""Connector Registry - WP-12 (MISSION-5.2 / IP-5.2-002).

Registry Connector (read/discovery, bukan execution).
"""
from __future__ import annotations

from typing import Optional, Tuple

from .connector_model import ToolConnector


class ConnectorRegistry:
    """Registry Connector."""

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
