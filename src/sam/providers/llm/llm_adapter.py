"""LLM Adapter — adapter generik untuk penyedia LLM (Sprint 229).

Program A — External Connector Integration.
LLMAdapter adalah kontrak yang DI-IMPLEMENTASIKAN oleh setiap penyedia LLM
(OpenAI, Anthropic, Gemini, DeepSeek, Ollama, OpenClaw). Semua penyedia
berbicara melalui interface yang sama.

Preview-first: `preview()` membangun request + response deterministik tanpa
network call. Eksekusi nyata diblokir secara eksplisit hingga mode execute.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from .llm_request import LLMRequest
from .llm_response import LLMResponse
from .llm_model import LLMModel
from .llm_session import LLMSession
from ..interfaces.provider_error import (
    ProviderError,
    ProviderErrorKind,
    ProviderException,
)


@dataclass(frozen=True)
class LLMAdapterResult:
    """Hasil operasi adapter (immutable)."""
    ok: bool
    response: Optional[LLMResponse] = None
    preview: bool = True
    external_calls: int = 0
    error: Optional[ProviderError] = None


class LLMAdapter(ABC):
    """Kontrak abstract untuk semua penyedia LLM.

    Subclass wajib implement: provider_id, models(), build_preview_payload(),
    parse_response().
    """

    provider_id: str = "unknown"

    @abstractmethod
    def models(self) -> list:
        """Daftar model yang didukung (read-only)."""

    @abstractmethod
    def build_preview_payload(self, request: LLMRequest) -> dict:
        """Membangun payload wire-format (tanpa network). Deterministik."""

    @abstractmethod
    def parse_response(self, payload: dict, request: LLMRequest) -> LLMResponse:
        """Mengubah payload respons mentah menjadi LLMResponse."""

    def preview(self, request: LLMRequest) -> LLMAdapterResult:
        """Mode preview: bangun payload, jangan panggil network, external_calls=0."""
        if request.mode != "preview":
            raise ProviderException(
                ProviderError(
                    code="PREVIEW_ONLY",
                    kind=ProviderErrorKind.PREVIEW_ONLY,
                    message="LLM provider preview-only; eksekusi diblokir",
                    provider_id=self.provider_id,
                    operation="preview",
                )
            )
        payload = self.build_preview_payload(request)
        response = self.parse_response(payload, request)
        return LLMAdapterResult(
            ok=True,
            response=response,
            preview=True,
            external_calls=0,
            error=None,
        )

    def generate(self, request: LLMRequest) -> LLMAdapterResult:
        """Block execution sampai approval; di sini hanya preview yang diizinkan."""
        return self.preview(request)
