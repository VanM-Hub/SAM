"""Gemini Adapter — implementasi LLMAdapter untuk Google Gemini (Sprint 232).

Preview-only: build payload wire-format + parsing response DETERMINISTIK
tanpa network call. External calls = 0 di mode preview. Eksekusi diblokir
sampai approval (mode execute).
"""
from __future__ import annotations
from typing import List

from ..llm.llm_adapter import LLMAdapter, LLMAdapterResult
from ..llm.llm_request import LLMRequest
from ..llm.llm_response import LLMResponse
from ..llm.llm_model import LLMModel, LLMModelCapability
from ..interfaces.provider_error import (
    ProviderError,
    ProviderErrorKind,
    ProviderException,
)

from .gemini_config import GeminiProviderConfig
from .gemini_request import GeminiRequest
from .gemini_response import GeminiResponse


class GeminiAdapter(LLMAdapter):
    """Adapter penyedia Gemini (preview-only)."""

    provider_id = "gemini"

    def __init__(self, config: "GeminiProviderConfig | None" = None) -> None:
        self._config = config or GeminiProviderConfig()

    def models(self) -> List[LLMModel]:
        return [
            LLMModel(
                model_id=mid,
                provider_id=self.provider_id,
                display_name=mid,
                capability=LLMModelCapability(
                    context_window=1000000 if "2.5" in mid else 32768,
                    supports_tools=True,
                    supports_vision=True,
                    supports_json=True,
                ),
                preview_only=True,
                external_calls=0,
            )
            for mid in self._config.models
        ]

    def build_preview_payload(self, request: LLMRequest) -> dict:
        model = self._config.resolve_model(request.model)
        gem = GeminiRequest.from_llm(request).as_dict()
        return {
            "provider": self.provider_id,
            "endpoint": f"/models/{model}:generateContent",
            "method": "POST",
            "contents": gem["contents"],
            "generationConfig": gem["generationConfig"],
            "_preview": True,
        }

    def parse_response(self, payload: dict, request: LLMRequest) -> LLMResponse:
        model = payload.get("model", request.model)
        candidates = payload.get("candidates", [])
        text = ""
        if candidates:
            first = candidates[0]
            if isinstance(first, dict):
                content = first.get("content", {})
                parts = content.get("parts", []) if isinstance(content, dict) else []
                for p in parts:
                    if isinstance(p, dict) and "text" in p:
                        text += p.get("text", "")
        usage_raw = payload.get("usageMetadata", {}) or {}
        usage = {
            "promptTokenCount": usage_raw.get("promptTokenCount", 0),
            "candidatesTokenCount": usage_raw.get("candidatesTokenCount", 0),
        }
        gem_resp = GeminiResponse(
            response_id="gem-" + request.request_id,
            request_id=request.request_id,
            model=model,
            text=text,
            finish_reason=(
                first.get("finishReason", "STOP") if candidates and isinstance(first, dict) else "STOP"
            ),
            usage=usage,
            provider_id=self.provider_id,
            external_calls=0,
        )
        return gem_resp.to_llm()

    def generate(self, request: LLMRequest) -> LLMAdapterResult:
        if request.mode != "preview":
            raise ProviderException(
                ProviderError(
                    code="GEMINI_EXEC_BLOCKED",
                    kind=ProviderErrorKind.PREVIEW_ONLY,
                    message="Gemini provider preview-only hingga approval",
                    provider_id=self.provider_id,
                    operation="generate",
                )
            )
        return self.preview(request)
