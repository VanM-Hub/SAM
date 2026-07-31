"""DeepSeek Adapter — implementasi LLMAdapter untuk DeepSeek (Sprint 233).

Preview-only: build payload wire-format + parsing response DETERMINISTIK
tanpa network call. External calls = 0 di mode preview. Eksekusi diblokir.
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

from .deepseek_config import DeepSeekProviderConfig
from .deepseek_request import DeepSeekRequest
from .deepseek_response import DeepSeekResponse


class DeepSeekAdapter(LLMAdapter):
    """Adapter penyedia DeepSeek (preview-only)."""

    provider_id = "deepseek"

    def __init__(self, config: "DeepSeekProviderConfig | None" = None) -> None:
        self._config = config or DeepSeekProviderConfig()

    def models(self) -> List[LLMModel]:
        return [
            LLMModel(
                model_id=mid,
                provider_id=self.provider_id,
                display_name=mid,
                capability=LLMModelCapability(
                    context_window=65536,
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
        ds = DeepSeekRequest.from_llm(request).as_dict()
        return {
            "provider": self.provider_id,
            "endpoint": "/chat/completions",
            "method": "POST",
            "model": model,
            "messages": ds["messages"],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "_preview": True,
        }

    def parse_response(self, payload: dict, request: LLMRequest) -> LLMResponse:
        model = payload.get("model", request.model)
        choices = payload.get("choices", [])
        text = ""
        finish_reason = "stop"
        if choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message", {})
                if isinstance(message, dict):
                    text = message.get("content", "") or ""
                finish_reason = first.get("finish_reason", "stop")
        usage = payload.get("usage", {}) or {}
        norm = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
        ds_resp = DeepSeekResponse(
            response_id="ds-" + request.request_id,
            request_id=request.request_id,
            model=model,
            text=text,
            finish_reason=finish_reason,
            usage=norm,
            provider_id=self.provider_id,
            external_calls=0,
        )
        return ds_resp.to_llm()

    def generate(self, request: LLMRequest) -> LLMAdapterResult:
        if request.mode != "preview":
            raise ProviderException(
                ProviderError(
                    code="DEEPSEEK_EXEC_BLOCKED",
                    kind=ProviderErrorKind.PREVIEW_ONLY,
                    message="DeepSeek provider preview-only hingga approval",
                    provider_id=self.provider_id,
                    operation="generate",
                )
            )
        return self.preview(request)
