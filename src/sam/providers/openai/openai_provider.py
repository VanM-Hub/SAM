"""OpenAI Adapter — implementasi LLMAdapter untuk OpenAI (Sprint 230).

Preview-only: build payload wire-format + parsing response DETERMINISTIK
tanpa network call. External calls selalu 0 di mode preview. Eksekusi nyata
diblokir sampai approval (mode execute) sesuai prinsip Program A.
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

from .openai_config import OpenAIProviderConfig
from .openai_request import OpenAIRequest
from .openai_response import OpenAIResponse


class OpenAIAdapter(LLMAdapter):
    """Adapter penyedia OpenAI (preview-only)."""

    provider_id = "openai"

    def __init__(self, config: OpenAIProviderConfig | None = None) -> None:
        self._config = config or OpenAIProviderConfig()

    def models(self) -> List[LLMModel]:
        """Daftar model OpenAI (read-only, preview)."""
        return [
            LLMModel(
                model_id=mid,
                provider_id=self.provider_id,
                display_name=mid,
                capability=LLMModelCapability(
                    context_window=128000 if "gpt-4o" in mid else 16384,
                    supports_tools=True,
                    supports_json=True,
                ),
                preview_only=True,
                external_calls=0,
            )
            for mid in self._config.models
        ]

    def build_preview_payload(self, request: LLMRequest) -> dict:
        """Bangun wire-format request OpenAI (deterministik, tanpa network)."""
        model = self._config.resolve_model(request.model)
        oai = OpenAIRequest.from_llm(request).as_dict()
        return {
            "provider": self.provider_id,
            "endpoint": "/chat/completions",
            "method": "POST",
            "model": model,
            "messages": oai["messages"],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "_preview": True,
        }

    def parse_response(self, payload: dict, request: LLMRequest) -> LLMResponse:
        """Ubah payload respons mentah menjadi LLMResponse generik."""
        model = payload.get("model", request.model)
        # Dalam preview, kita tidak benar-benar memanggil API; gunakan payload.
        text = payload.get("content", "") or payload.get("text", "")
        usage_raw = payload.get("usage", {})
        usage = {
            "prompt_tokens": usage_raw.get("prompt_tokens", 0),
            "completion_tokens": usage_raw.get("completion_tokens", 0),
            "total_tokens": usage_raw.get("total_tokens", 0),
        }
        oai_resp = OpenAIResponse(
            response_id="oai-" + request.request_id,
            request_id=request.request_id,
            model=model,
            text=text,
            finish_reason=payload.get("finish_reason", "stop"),
            usage=usage,
            provider_id=self.provider_id,
            external_calls=0,
        )
        return oai_resp.to_llm()

    def generate(self, request: LLMRequest) -> LLMAdapterResult:
        """Preview deterministik; eksekusi nyata diblokir di sini."""
        if request.mode != "preview":
            raise ProviderException(
                ProviderError(
                    code="OPENAI_EXEC_BLOCKED",
                    kind=ProviderErrorKind.PREVIEW_ONLY,
                    message="OpenAI provider preview-only hingga approval",
                    provider_id=self.provider_id,
                    operation="generate",
                )
            )
        return self.preview(request)
