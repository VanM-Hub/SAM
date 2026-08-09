"""Provider Adapter Framework - WP-11 (MISSION-5.1 / IP-5.1-002).

Abstraction layer untuk seluruh Provider Adapter. Normalisasi request/response/
error lintas provider. Adapter tidak mengekspos SDK vendor ke domain SAM.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional
from enum import Enum


class ConnectionStatus(str, Enum):
    """Status koneksi adapter."""

    UNKNOWN = "unknown"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass(frozen=True)
class ProviderRequest:
    """Request yang dinormalisasi menuju provider."""

    provider_id: str
    prompt: str
    model_id: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "prompt": self.prompt,
            "model_id": self.model_id,
            "parameters": dict(self.parameters),
        }


@dataclass(frozen=True)
class NormalizedResponse:
    """Response yang dinormalisasi dari provider."""

    text: str
    provider_id: str
    model_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    finish_status: str = "complete"
    structured: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "text": self.text,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "metadata": dict(self.metadata),
            "finish_status": self.finish_status,
            "structured": self.structured,
            "error": self.error,
        }


class ProviderAdapterError(Exception):
    """Error ter-normalisasi dari provider."""

    def __init__(self, provider_id: str, code: str, message: str) -> None:
        super().__init__(message)
        self.provider_id = provider_id
        self.code = code
        self.message = message


class ProviderAdapter:
    """Kontrak adapter provider. Subclass mengimplementasikan mapping."""

    provider_id: str = ""
    provider_name: str = ""

    def __init__(self) -> None:
        self._status = ConnectionStatus.UNKNOWN
        self._connection_fn: Optional[Callable[[], bool]] = None

    def bind(self, connection_fn: Optional[Callable[[], bool]] = None) -> None:
        """Binding koneksi (maksimal verifikasi status, bukan eksekusi domain)."""
        self._connection_fn = connection_fn

    def connect(self) -> ConnectionStatus:
        if self._connection_fn is None:
            self._status = ConnectionStatus.CONNECTED
        else:
            try:
                ok = self._connection_fn()
                self._status = ConnectionStatus.CONNECTED if ok else ConnectionStatus.ERROR
            except Exception:
                self._status = ConnectionStatus.ERROR
        return self._status

    @property
    def status(self) -> ConnectionStatus:
        return self._status

    def invoke(self, request: ProviderRequest) -> NormalizedResponse:
        """Menerjemahkan request SAM -> panggil provider -> normalisasi response.

        Implementasi subclass menerjemahkan SDK provider secara internal tanpa
        mengekspos SDK tersebut ke luar.
        """
        raise NotImplementedError

    def map_error(self, exc: Exception) -> ProviderAdapterError:
        return ProviderAdapterError(self.provider_id, "provider_error", str(exc))
