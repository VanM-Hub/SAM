"""Provider Error — kesalahan domain standar provider (Sprint 228).

Program A — External Connector Integration.
Enum + exception generik yang dipakai seluruh provider. Immutable, deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ProviderErrorKind(str, Enum):
    """Kategori kesalahan provider (deterministik)."""
    NOT_SUPPORTED = "not_supported"
    INVALID_REQUEST = "invalid_request"
    INVALID_RESPONSE = "invalid_response"
    UNAUTHORIZED = "unauthorized"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PREVIEW_ONLY = "preview_only"
    EXECUTION_BLOCKED = "execution_blocked"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProviderError:
    """Representasi immutable sebuah kesalahan provider."""
    code: str
    kind: ProviderErrorKind
    message: str
    provider_id: str = "unknown"
    operation: str = "unknown"
    retryable: bool = False
    recovery: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "kind": self.kind.value,
            "message": self.message,
            "provider_id": self.provider_id,
            "operation": self.operation,
            "retryable": self.retryable,
            "recovery": self.recovery,
        }


class ProviderException(Exception):
    """Exception runtime yang membawa ProviderError.

    Digunakan oleh Preview/Provider adapter tanpa melakukan network call.
    """

    def __init__(self, error: ProviderError) -> None:
        super().__init__(error.message)
        self.error = error

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"[{self.error.kind.value}] {self.error.message}"
