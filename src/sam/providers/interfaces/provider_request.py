"""Provider Request — request standar menuju provider (Sprint 228).

Program A — External Connector Integration.
Interface generik: request yang dikirim lewat Connector Runtime ke Provider Runtime.
Preview-first, immutable, no provider-specific field.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ProviderRequest:
    """Request standar ke provider. Immutable, preview-first, external_calls=0."""
    request_id: str
    provider_id: str
    operation: str
    payload: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: float = 30.0
    mode: str = "preview"  # preview | approval | execute
    external_calls: int = 0  # selalu 0 di mode preview

    def as_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "provider_id": self.provider_id,
            "operation": self.operation,
            "payload": dict(self.payload),
            "headers": dict(self.headers),
            "parameters": dict(self.parameters),
            "timeout_seconds": self.timeout_seconds,
            "mode": self.mode,
            "external_calls": self.external_calls,
        }


@dataclass(frozen=True)
class ProviderRequestBuilder:
    """Builder deterministik untuk ProviderRequest."""
    request_id: str
    provider_id: str
    operation: str
    _payload: Dict[str, Any] = field(default_factory=dict)
    _headers: Dict[str, str] = field(default_factory=dict)
    _parameters: Dict[str, Any] = field(default_factory=dict)
    _timeout: float = 30.0
    _mode: str = "preview"

    def with_payload(self, payload: Dict[str, Any]) -> "ProviderRequestBuilder":
        merged = dict(self._payload)
        merged.update(payload)
        return ProviderRequestBuilder(
            self.request_id, self.provider_id, self.operation, merged,
            self._headers, self._parameters, self._timeout, self._mode,
        )

    def with_header(self, key: str, value: str) -> "ProviderRequestBuilder":
        headers = dict(self._headers)
        headers[key] = value
        return ProviderRequestBuilder(
            self.request_id, self.provider_id, self.operation, self._payload,
            headers, self._parameters, self._timeout, self._mode,
        )

    def with_parameter(self, key: str, value: Any) -> "ProviderRequestBuilder":
        params = dict(self._parameters)
        params[key] = value
        return ProviderRequestBuilder(
            self.request_id, self.provider_id, self.operation, self._payload,
            self._headers, params, self._timeout, self._mode,
        )

    def in_mode(self, mode: str) -> "ProviderRequestBuilder":
        return ProviderRequestBuilder(
            self.request_id, self.provider_id, self.operation, self._payload,
            self._headers, self._parameters, self._timeout, mode,
        )

    def with_timeout(self, seconds: float) -> "ProviderRequestBuilder":
        return ProviderRequestBuilder(
            self.request_id, self.provider_id, self.operation, self._payload,
            self._headers, self._parameters, seconds, self._mode,
        )

    def build(self) -> ProviderRequest:
        calls = 0 if self._mode == "preview" else 0  # default external_calls=0
        return ProviderRequest(
            request_id=self.request_id,
            provider_id=self.provider_id,
            operation=self.operation,
            payload=dict(self._payload),
            headers=dict(self._headers),
            parameters=dict(self._parameters),
            timeout_seconds=self._timeout,
            mode=self._mode,
            external_calls=calls,
        )
