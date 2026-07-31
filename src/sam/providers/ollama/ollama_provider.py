"""Ollama Adapter — implementasi LLMAdapter untuk Ollama (Sprint 234).

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

from .ollama_config import OllamaProviderConfig
from .ollama_request import OllamaRequest
from .ollama_response import OllamaResponse


class OllamaAdapter(LLMAdapter):
    """Adapter penyedia Ollama (preview-only, model lokal)."""

    provider_id = "ollama"

    def __init__(self, config: "OllamaProviderConfig | None" = None) -> None:
        self._config = config or OllamaProviderConfig()

    def models(self) -> List[LLMModel]:
        return [
            LLMModel(
                model_id=mid,
                provider_id=self.provider_id,
                display_name=mid,
                capability=LLMModelCapability(
                    context_window=32768,
                    supports_tools=False,
                    supports_json=True,
                ),
                preview_only=True,
                external_calls=0,
            )
            for mid in self._config.models
        ]

    def build_preview_payload(self, request: LLMRequest) -> dict:
        model = self._config.resolve_model(request.model)
        ol = OllamaRequest.from_llm(request).as_dict()
        return {
            "provider": self.provider_id,
            "endpoint": "/api/generate",
            "method": "POST",
            "model": model,
            "prompt": ol["prompt"],
            "options": ol["options"],
            "stream": False,
            "_preview": True,
        }

    def parse_response(self, payload: dict, request: LLMRequest) -> LLMResponse:
        model = payload.get("model", request.model)
        text = payload.get("response", "") or payload.get("text", "")
        ol_resp = OllamaResponse(
            response_id="ollama-" + request.request_id,
            request_id=request.request_id,
            model=model,
            text=text,
            done=payload.get("done", True),
            eval_count=payload.get("eval_count", 0),
            prompt_eval_count=payload.get("prompt_eval_count", 0),
            provider_id=self.provider_id,
            external_calls=0,
        )
        return ol_resp.to_llm()

    def generate(self, request: LLMRequest) -> LLMAdapterResult:
        if request.mode != "preview":
            raise ProviderException(
                ProviderError(
                    code="OLLAMA_EXEC_BLOCKED",
                    kind=ProviderErrorKind.PREVIEW_ONLY,
                    message="Ollama provider preview-only hingga approval",
                    provider_id=self.provider_id,
                    operation="generate",
                )
            )
        return self.preview(request)
