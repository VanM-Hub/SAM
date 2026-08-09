"""Anthropic Adapter - WP-13 (MISSION-5.1 / IP-5.1-002).

Adapter Anthropic melalui Provider Contract yang sama. Consumer SAM tidak
mengetahui detail implementasi Anthropic.
"""
from __future__ import annotations

from typing import Callable, Optional

from .adapter_framework import (
    NormalizedResponse,
    ProviderAdapter,
    ProviderAdapterError,
    ProviderRequest,
)


class AnthropicAdapter(ProviderAdapter):
    """Adapter untuk Anthropic."""

    provider_id = "anthropic"
    provider_name = "Anthropic"

    def __init__(self, transport: Optional[Callable[[dict], dict]] = None) -> None:
        super().__init__()
        self._transport = transport

    def invoke(self, request: ProviderRequest) -> NormalizedResponse:
        payload = {
            "model": request.model_id or "claude-3-5-sonnet",
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.parameters.get("max_tokens", 1024),
        }
        try:
            raw = self._transport(payload) if self._transport else self._mock(payload)
            return self._normalize(raw)
        except Exception as exc:  # noqa: BLE001
            raise self.map_error(exc)

    @staticmethod
    def _mock(payload: dict) -> dict:  # pragma: no cover
        return {"content": [{"text": "anthropic-mock-response"}], "model": payload["model"]}

    def _normalize(self, raw: dict) -> NormalizedResponse:
        try:
            text = "".join(c.get("text", "") for c in raw["content"] if isinstance(c, dict))
        except (KeyError, TypeError):
            raise ProviderAdapterError(self.provider_id, "invalid_response", "content missing")
        return NormalizedResponse(
            text=text,
            provider_id=self.provider_id,
            model_id=str(raw.get("model", "")),
        )

    def map_error(self, exc: Exception) -> ProviderAdapterError:
        return ProviderAdapterError(self.provider_id, "anthropic_error", str(exc))
