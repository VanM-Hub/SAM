"""Provider Response — response standar dari provider (Sprint 228).

Program A — External Connector Integration.
Interface generik: response yang diterima Connector Runtime dari Provider Runtime.
Immutable, deterministik, preview-first.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ProviderResponse:
    """Response standar dari provider. Immutable, preview-first."""
    response_id: str
    request_id: str
    provider_id: str
    operation: str
    ok: bool = True
    data: Dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    latency_ms: float = 0.0
    mode: str = "preview"
    external_calls: int = 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "response_id": self.response_id,
            "request_id": self.request_id,
            "provider_id": self.provider_id,
            "operation": self.operation,
            "ok": self.ok,
            "data": dict(self.data),
            "error_code": self.error_code,
            "error_message": self.error_message,
            "latency_ms": self.latency_ms,
            "mode": self.mode,
            "external_calls": self.external_calls,
        }


@dataclass(frozen=True)
class ProviderResponseBuilder:
    """Builder deterministik untuk ProviderResponse."""
    response_id: str
    request_id: str
    provider_id: str
    operation: str
    _data: Dict[str, Any] = field(default_factory=dict)
    _error_code: Optional[str] = None
    _error_message: Optional[str] = None
    _latency: float = 0.0
    _mode: str = "preview"

    def with_data(self, data: Dict[str, Any]) -> "ProviderResponseBuilder":
        merged = dict(self._data)
        merged.update(data)
        return ProviderResponseBuilder(
            self.response_id, self.request_id, self.provider_id, self.operation,
            merged, self._error_code, self._error_message, self._latency, self._mode,
        )

    def failed(self, code: str, message: str) -> "ProviderResponseBuilder":
        return ProviderResponseBuilder(
            self.response_id, self.request_id, self.provider_id, self.operation,
            self._data, code, message, self._latency, self._mode,
        )

    def with_latency(self, ms: float) -> "ProviderResponseBuilder":
        return ProviderResponseBuilder(
            self.response_id, self.request_id, self.provider_id, self.operation,
            self._data, self._error_code, self._error_message, ms, self._mode,
        )

    def in_mode(self, mode: str) -> "ProviderResponseBuilder":
        return ProviderResponseBuilder(
            self.response_id, self.request_id, self.provider_id, self.operation,
            self._data, self._error_code, self._error_message, self._latency, mode,
        )

    def build(self) -> ProviderResponse:
        if self._error_code is not None:
            return ProviderResponse(
                response_id=self.response_id,
                request_id=self.request_id,
                provider_id=self.provider_id,
                operation=self.operation,
                ok=False,
                data=dict(self._data),
                error_code=self._error_code,
                error_message=self._error_message,
                latency_ms=self._latency,
                mode=self._mode,
                external_calls=0,
            )
        return ProviderResponse(
            response_id=self.response_id,
            request_id=self.request_id,
            provider_id=self.provider_id,
            operation=self.operation,
            ok=True,
            data=dict(self._data),
            error_code=None,
            error_message=None,
            latency_ms=self._latency,
            mode=self._mode,
            external_calls=0,
        )
