"""Connector Model - WP-11 (MISSION-5.2 / IP-5.2-002).

Model Connector yang memisahkan Tool domain dari transport & vendor
implementation. Connector adalah boundary antara SAM dan dunia eksternal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Optional, Tuple


class ConnectorType(str, Enum):
    """Jenis transport connector."""

    HTTP_API = "http_api"
    LOCAL_PROCESS = "local_process"
    SDK_ADAPTER = "sdk_adapter"


class ConnectorState(str, Enum):
    """Keadaan lifecycle connector."""

    CREATED = "created"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class ConnectorHandle:
    """Handle connector stateless (deskripsi + status)."""

    connector_id: str
    tool_id: str
    connector_type: ConnectorType
    endpoint: str = ""
    state: ConnectorState = ConnectorState.CREATED
    created_at: str = field(default_factory=_now_utc)
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "connector_id": self.connector_id,
            "tool_id": self.tool_id,
            "connector_type": self.connector_type.value,
            "endpoint": self.endpoint,
            "state": self.state.value,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


class ToolConnector:
    """Connector menjembatani Tool Citizen dengan transport eksternal.

    Transport function di-inject sehingga connector-specific logic tetap pada
    integration boundary; SDK vendor tidak bocor ke domain.
    """

    def __init__(
        self,
        handle: ConnectorHandle,
        transport: Optional[Callable[[dict], dict]] = None,
    ) -> None:
        self.handle = handle
        self._transport = transport
        self._bound_credential_ref: Optional[str] = None

    @property
    def connected(self) -> bool:
        return self.handle.state == ConnectorState.CONNECTED

    def bind_credential(self, credential_ref: str) -> None:
        """Mengikat referensi credential (bukan nilai credential itu sendiri)."""
        self._bound_credential_ref = credential_ref

    @property
    def credential_ref(self) -> Optional[str]:
        return self._bound_credential_ref

    def call(self, request: dict) -> dict:
        """Memanggil transport eksternal. Mengembalikan raw response."""
        if self._transport is None:
            return {"_mock": True, "response": "connector-mock"}
        return self._transport(request)
