"""OpenAI Adapter - WP-12 (MISSION-5.1 / IP-5.1-002).

Adapter OpenAI melalui Provider Contract. Menggunakan transport function
yang di-inject sehingga dapat diuji tanpa menjadikan OpenAI dependency domain.
"""
from __future__ import annotations

from typing import Callable, Optional

from .adapter_framework import (
    NormalizedResponse,
    ProviderAdapter,
    ProviderAdapterError,
    ProviderRequest,
)


class OpenAIAdapter(ProviderAdapter):
    """Adapter untuk OpenAI."""

    provider_id = "openai"
    provider_name = "OpenAI"

    def __init__(self, transport: Optional[Callable[[dict], dict]] = None) -> None:
        super().__init__()
        self._transport = transport

    def invoke(self, request: ProviderRequest) -> NormalizedResponse:
        payload = {
            "model": request.model_id or "gpt-4o-mini",
            "messages": [{"role": "user", "content": request.prompt}],
            **request.parameters,
        }
        try:
            if self._transport is not None:
                raw = self._transport(payload)
            else:
                raw = self._mock(payload)
            return self._normalize(raw)
        except Exception as exc:  # noqa: BLE001
            raise self.map_error(exc)

    @staticmethod
    def _mock(payload: dict) -> dict:  # pragma: no cover - mock default
        return {
            "choices": [{"message": {"content": "openai-mock-response"}}],
            "model": payload["model"],
            "usage": {"total_tokens": 12},
        }

    def _normalize(self, raw: dict) -> NormalizedResponse:
        try:
            text = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise ProviderAdapterError(
                self.provider_id, "invalid_response", "choices missing"
            )
        return NormalizedResponse(
            text=text,
            provider_id=self.provider_id,
            model_id=str(raw.get("model", "")),
            metadata={"usage": raw.get("usage", {})},
        )

    def map_error(self, exc: Exception) -> ProviderAdapterError:
        return ProviderAdapterError(self.provider_id, "openai_error", str(exc))
