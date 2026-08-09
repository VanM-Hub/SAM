"""Connection Management & Credential Binding - WP-14/WP-15 (MISSION-5.2 / IP-5.2-002).

Mengelola koneksi connector dan mengikat referensi credential dengan aman.
Credential TIDAK disimpan pada Tool domain; hanya referensi.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple


class ConnectionState(str, Enum):
    """Keadaan koneksi."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class ConnectionRecord:
    """Rekam koneksi connector (read-only)."""

    connector_id: str
    state: ConnectionState = ConnectionState.DISCONNECTED
    established_at: Optional[str] = None
    error: str = ""

    @property
    def connected(self) -> bool:
        return self.state == ConnectionState.CONNECTED

    def as_dict(self) -> dict:
        return {
            "connector_id": self.connector_id,
            "state": self.state.value,
            "established_at": self.established_at,
            "error": self.error,
            "connected": self.connected,
        }


class ConnectionManager:
    """Mengelola koneksi connector."""

    def __init__(self) -> None:
        self._records: dict = {}

    def connect(self, connector_id: str) -> ConnectionRecord:
        record = ConnectionRecord(
            connector_id=connector_id, state=ConnectionState.CONNECTED, established_at=_now_utc()
        )
        self._records[connector_id] = record
        return record

    def fail(self, connector_id: str, error: str) -> ConnectionRecord:
        record = ConnectionRecord(connector_id=connector_id, state=ConnectionState.FAILED, error=error)
        self._records[connector_id] = record
        return record

    def disconnect(self, connector_id: str) -> ConnectionRecord:
        record = ConnectionRecord(connector_id=connector_id, state=ConnectionState.DISCONNECTED)
        self._records[connector_id] = record
        return record

    def status(self, connector_id: str) -> Optional[ConnectionRecord]:
        return self._records.get(connector_id)

    def all_connected(self) -> Tuple[ConnectionRecord, ...]:
        return tuple(r for r in self._records.values() if r.connected)


@dataclass(frozen=True)
class CredentialBinding:
    """Ikatan referensi credential ke connector (TANPA nilai credential)."""

    connector_id: str
    credential_ref: str
    bound_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "connector_id": self.connector_id,
            "credential_ref": self.credential_ref,
            "bound_at": self.bound_at,
            "has_secret_value": False,
        }


class CredentialBinder:
    """Mengikat referensi credential. Tidak pernah menyimpan nilai secret."""

    def __init__(self) -> None:
        self._bindings: dict = {}

    def bind(self, connector_id: str, credential_ref: str) -> CredentialBinding:
        binding = CredentialBinding(connector_id=connector_id, credential_ref=credential_ref)
        self._bindings[connector_id] = binding
        return binding

    def binding_for(self, connector_id: str) -> Optional[CredentialBinding]:
        return self._bindings.get(connector_id)

    @staticmethod
    def never_exposes_secret(binding: CredentialBinding) -> bool:
        return "secret" not in binding.as_dict() and not binding.as_dict()["has_secret_value"]
