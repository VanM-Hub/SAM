"""Connector Bridge — bridge model <-> connector (read-only) (Sprint 249).

Program B — Model Runtime Integration.
Read-only bridge ke Connector Runtime; tidak ada eksekusi connector.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..connectors.connector_descriptor import ConnectorDescriptor


@dataclass(frozen=True)
class ConnectorBridgeView:
    """View read-only connector (immutable)."""
    connector_name: str
    connected: bool = False
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "connector_name": self.connector_name,
            "connected": self.connected,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ConnectorBridge:
    """Bridge model <-> connector. Read-only, tidak menjalankan connector."""

    def view(self, descriptor: ConnectorDescriptor) -> ConnectorBridgeView:
        return ConnectorBridgeView(
            connector_name=descriptor.name,
            connected=False,  # no actual connection in preview
            preview_only=True,
            external_calls=0,
        )
