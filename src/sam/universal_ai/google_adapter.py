"""Google AI Adapter - WP-14 (MISSION-5.1 / IP-5.1-002).

Adapter Google AI (Gemini) melalui Provider Contract. Mengikuti contract yang
sama dengan Provider lain.
"""
from __future__ import annotations

from typing import Callable, Optional

from .adapter_framework import (
    NormalizedResponse,
    ProviderAdapter,
    ProviderAdapterError,
    ProviderRequest,
)


class GoogleAIAdapter(ProviderAdapter):
    """Adapter untuk Google AI / Gemini."""

    provider_id = "google_ai"
    provider_name = "Google AI"

    def __init__(self, transport: Optional[Callable[[dict], dict]] = None) -> None:
        super().__init__()
        self._transport = transport

    def invoke(self, request: ProviderRequest) -> NormalizedResponse:
        payload = {
            "model": request.model_id or "gemini-1.5-pro",
            "contents": [{"parts": [{"text": request.prompt}]}],
        }
        try:
            raw = self._transport(payload) if self._transport else self._mock(payload)
            return self._normalize(raw)
        except Exception as exc:  # noqa: BLE001
            raise self.map_error(exc)

    @staticmethod
    def _mock(payload: dict) -> dict:  # pragma: no cover
        return {"candidates": [{"content": {"parts": [{"text": "google-mock-response"}]}}], "model": payload["model"]}

    def _normalize(self, raw: dict) -> NormalizedResponse:
        try:
            parts = raw["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
        except (KeyError, IndexError, TypeError):
            raise ProviderAdapterError(self.provider_id, "invalid_response", "candidates missing")
        return NormalizedResponse(
            text=text,
            provider_id=self.provider_id,
            model_id=str(raw.get("model", "")),
        )

    def map_error(self, exc: Exception) -> ProviderAdapterError:
        return ProviderAdapterError(self.provider_id, "google_error", str(exc))
