"""
OP-282 — LLM Gateway

Memilih dan mengelola provider.
Gateway hanya mengenal interface ReasoningProvider.
Tidak ada import Domain, Repository, atau MissionController.
"""

from __future__ import annotations
from typing import Any
from datetime import datetime

from .provider import (
    ReasoningProvider, ReasoningRequest, ReasoningResponse,
    ProviderMetadata, UsageMetrics,
)


# ── Provider Implementations ─────────────────────────────────────────

_MOCK_COUNT: int = 0


class MockProvider:
    """Provider untuk testing tanpa network call."""

    def __init__(self, model_name: str = "mock-model-v1") -> None:
        self._model = model_name
        self._healthy = True

    def generate(self, request: ReasoningRequest) -> ReasoningResponse:
        global _MOCK_COUNT
        _MOCK_COUNT += 1
        ans = f"MOCK response to: {request.prompt[:60]}"
        return ReasoningResponse(
            answer=ans,
            confidence=0.95,
            provider="mock",
            model=self._model,
            usage=UsageMetrics(prompt_tokens=len(request.prompt),
                               completion_tokens=len(ans),
                               total_tokens=len(request.prompt) + len(ans)),
            latency_ms=0.5,
            warnings=(),
        )

    def stream(self, request: ReasoningRequest):
        yield "mock chunk"

    def health(self) -> bool:
        return self._healthy

    def set_health(self, healthy: bool) -> None:
        self._healthy = healthy

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            provider_name="mock",
            model_name=self._model,
            version="1.0.0",
            supports_streaming=True,
            supports_json=True,
        )

    def close(self) -> None:
        pass


class OpenAIProvider:
    """Stub — placeholder untuk implementasi nyata."""

    def __init__(self, model_name: str = "gpt-4o", api_key: str = "") -> None:
        self._model = model_name
        self._api_key = api_key

    def generate(self, request: ReasoningRequest) -> ReasoningResponse:
        # Stub: return fake response
        return ReasoningResponse(
            answer=f"[OpenAI stub] {request.prompt[:60]}",
            confidence=0.90,
            provider="openai",
            model=self._model,
            usage=UsageMetrics(prompt_tokens=100, completion_tokens=50),
            latency_ms=2.0,
        )

    def stream(self, request: ReasoningRequest):
        yield "[OpenAI stub chunk]"

    def health(self) -> bool:
        return True

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            provider_name="openai",
            model_name=self._model,
            version="1.0.0",
            supports_streaming=True,
            supports_vision=True,
            supports_json=True,
        )

    def close(self) -> None:
        pass


class GeminiProvider:
    """Stub — placeholder untuk Gemini."""

    def __init__(self, model_name: str = "gemini-2.0-flash", api_key: str = "") -> None:
        self._model = model_name
        self._api_key = api_key

    def generate(self, request: ReasoningRequest) -> ReasoningResponse:
        return ReasoningResponse(
            answer=f"[Gemini stub] {request.prompt[:60]}",
            confidence=0.88,
            provider="gemini",
            model=self._model,
            usage=UsageMetrics(prompt_tokens=100, completion_tokens=40),
            latency_ms=2.5,
        )

    def stream(self, request: ReasoningRequest):
        yield "[Gemini stub chunk]"

    def health(self) -> bool:
        return True

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            provider_name="gemini",
            model_name=self._model,
            version="1.0.0",
            supports_streaming=True,
            supports_vision=True,
            supports_json=True,
        )

    def close(self) -> None:
        pass


class ClaudeProvider:
    """Stub — placeholder untuk Claude."""

    def __init__(self, model_name: str = "claude-sonnet-4", api_key: str = "") -> None:
        self._model = model_name
        self._api_key = api_key

    def generate(self, request: ReasoningRequest) -> ReasoningResponse:
        return ReasoningResponse(
            answer=f"[Claude stub] {request.prompt[:60]}",
            confidence=0.92,
            provider="claude",
            model=self._model,
            usage=UsageMetrics(prompt_tokens=120, completion_tokens=55),
            latency_ms=3.0,
        )

    def stream(self, request: ReasoningRequest):
        yield "[Claude stub chunk]"

    def health(self) -> bool:
        return True

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            provider_name="claude",
            model_name=self._model,
            version="1.0.0",
            supports_streaming=True,
            supports_tools=True,
            supports_vision=True,
            supports_json=True,
        )

    def close(self) -> None:
        pass


class OllamaProvider:
    """Stub — placeholder untuk Ollama (local LLM)."""

    def __init__(self, model_name: str = "llama3", base_url: str = "http://localhost:11434") -> None:
        self._model = model_name
        self._base_url = base_url

    def generate(self, request: ReasoningRequest) -> ReasoningResponse:
        return ReasoningResponse(
            answer=f"[Ollama stub] {request.prompt[:60]}",
            confidence=0.85,
            provider="ollama",
            model=self._model,
            usage=UsageMetrics(prompt_tokens=100, completion_tokens=45),
            latency_ms=4.0,
        )

    def stream(self, request: ReasoningRequest):
        yield "[Ollama stub chunk]"

    def health(self) -> bool:
        return True

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            provider_name="ollama",
            model_name=self._model,
            version="1.0.0",
            supports_streaming=True,
            supports_json=True,
        )

    def close(self) -> None:
        pass


# ── Gateway ──────────────────────────────────────────────────────────

class LLMGateway:
    """
    Gateway untuk memilih dan mengelola provider.

    Pre-registered providers:
      - mock (default)
      - openai
      - gemini
      - claude
      - ollama
    """

    def __init__(self) -> None:
        self._providers: dict[str, ReasoningProvider] = {
            "mock": MockProvider(),
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(),
            "claude": ClaudeProvider(),
            "ollama": OllamaProvider(),
        }
        self._default: str = "mock"

    @property
    def provider_names(self) -> tuple[str, ...]:
        return tuple(self._providers.keys())

    def register(self, name: str, provider: ReasoningProvider) -> None:
        self._providers[name] = provider

    def get(self, name: str | None = None) -> ReasoningProvider:
        key = name or self._default
        if key not in self._providers:
            raise ValueError(f"Unknown provider: {key}. Available: {self.provider_names}")
        return self._providers[key]

    def set_default(self, name: str) -> None:
        if name not in self._providers:
            raise ValueError(f"Unknown provider: {name}")
        self._default = name

    def health(self) -> dict[str, bool]:
        return {name: p.health() for name, p in self._providers.items()}

    def generate(self, request: ReasoningRequest,
                 provider_name: str | None = None) -> ReasoningResponse:
        provider = self.get(provider_name or request.provider_hint or None)
        return provider.generate(request)

    def metadata(self, provider_name: str | None = None) -> ProviderMetadata:
        return self.get(provider_name).metadata()

    def list_metadata(self) -> dict[str, ProviderMetadata]:
        return {name: p.metadata() for name, p in self._providers.items()}
