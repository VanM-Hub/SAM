"""Local Model Adapter - WP-15 (MISSION-5.1 / IP-5.1-002).

Adapter untuk model lokal. Local Provider memiliki status yang sama secara
arsitektural dengan remote Provider.
"""
from __future__ import annotations

from typing import Callable, Optional

from .adapter_framework import (
    NormalizedResponse,
    ProviderAdapter,
    ProviderAdapterError,
    ProviderRequest,
)


class LocalModelAdapter(ProviderAdapter):
    """Adapter untuk model lokal (Ollama/LM Studio atau runtime lokal)."""

    provider_id = "local_model"
    provider_name = "Local Model"

    def __init__(self, transport: Optional[Callable[[dict], dict]] = None) -> None:
        super().__init__()
        self._transport = transport

    def invoke(self, request: ProviderRequest) -> NormalizedResponse:
        payload = {
            "model": request.model_id or "local-llm",
            "prompt": request.prompt,
        }
        try:
            raw = self._transport(payload) if self._transport else self._mock(payload)
            return self._normalize(raw)
        except Exception as exc:  # noqa: BLE001
            raise self.map_error(exc)

    @staticmethod
    def _mock(payload: dict) -> dict:  # pragma: no cover
        return {"response": "local-mock-response", "model": payload["model"]}

    def _normalize(self, raw: dict) -> NormalizedResponse:
        try:
            text = raw.get("response", "")
        except AttributeError:
            raise ProviderAdapterError(self.provider_id, "invalid_response", "response missing")
        return NormalizedResponse(
            text=text,
            provider_id=self.provider_id,
            model_id=str(raw.get("model", "")),
        )

    def map_error(self, exc: Exception) -> ProviderAdapterError:
        return ProviderAdapterError(self.provider_id, "local_error", str(exc))
