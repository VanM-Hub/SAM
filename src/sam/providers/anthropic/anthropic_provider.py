"""Anthropic Adapter — implementasi LLMAdapter untuk Anthropic (Sprint 231).

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

from .anthropic_config import AnthropicProviderConfig
from .anthropic_request import AnthropicRequest
from .anthropic_response import AnthropicResponse


class AnthropicAdapter(LLMAdapter):
    """Adapter penyedia Anthropic (preview-only)."""

    provider_id = "anthropic"

    def __init__(self, config: "AnthropicProviderConfig | None" = None) -> None:
        self._config = config or AnthropicProviderConfig()

    def models(self) -> List[LLMModel]:
        return [
            LLMModel(
                model_id=mid,
                provider_id=self.provider_id,
                display_name=mid,
                capability=LLMModelCapability(
                    context_window=200000,
                    supports_tools=True,
                    supports_json=True,
                ),
                preview_only=True,
                external_calls=0,
            )
            for mid in self._config.models
        ]

    def build_preview_payload(self, request: LLMRequest) -> dict:
        model = self._config.resolve_model(request.model)
        anc = AnthropicRequest.from_llm(request).as_dict()
        return {
            "provider": self.provider_id,
            "endpoint": "/messages",
            "method": "POST",
            "model": model,
            "messages": anc["messages"],
            "system": anc["system"],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "_preview": True,
        }

    def parse_response(self, payload: dict, request: LLMRequest) -> LLMResponse:
        model = payload.get("model", request.model)
        content = payload.get("content", [])
        # Anthropic content adalah list blok; ambil blok text deterministik.
        text = ""
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text += block.get("text", "")
        else:
            text = str(content or "")
        usage_raw = payload.get("usage", {}) or {}
        usage = {
            "prompt_tokens": usage_raw.get("input_tokens", 0),
            "completion_tokens": usage_raw.get("output_tokens", 0),
            "total_tokens": (
                usage_raw.get("input_tokens", 0)
                + usage_raw.get("output_tokens", 0)
            ),
        }
        anc_resp = AnthropicResponse(
            response_id="anc-" + request.request_id,
            request_id=request.request_id,
            model=model,
            text=text,
            stop_reason=payload.get("stop_reason", "end_turn"),
            usage=usage,
            provider_id=self.provider_id,
            external_calls=0,
        )
        return anc_resp.to_llm()

    def generate(self, request: LLMRequest) -> LLMAdapterResult:
        if request.mode != "preview":
            raise ProviderException(
                ProviderError(
                    code="ANTHROPIC_EXEC_BLOCKED",
                    kind=ProviderErrorKind.PREVIEW_ONLY,
                    message="Anthropic provider preview-only hingga approval",
                    provider_id=self.provider_id,
                    operation="generate",
                )
            )
        return self.preview(request)
