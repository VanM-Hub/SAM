"""
OP-281 — Reasoning Provider Protocol

Abstract protocol + DTO untuk semua LLM provider.

Tidak mengandung Domain, Repository, Storage, atau MissionController.
Provider hanya menerima PromptContext dan menghasilkan ReasoningResponse.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable
from abc import abstractmethod


# ── DTOs ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class UsageMetrics:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": self.cost_usd,
        }


@dataclass(frozen=True)
class ProviderMetadata:
    provider_name: str
    model_name: str
    version: str = ""
    supports_streaming: bool = False
    supports_tools: bool = False
    supports_vision: bool = False
    supports_json: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "model_name": self.model_name,
            "version": self.version,
            "supports_streaming": self.supports_streaming,
            "supports_tools": self.supports_tools,
            "supports_vision": self.supports_vision,
            "supports_json": self.supports_json,
        }


@dataclass(frozen=True)
class ReasoningRequest:
    prompt: str
    system_prompt: str = ""
    temperature: float = 0.0
    max_tokens: int = 2000
    stop_sequences: tuple[str, ...] = ()
    response_format: str = "text"  # text | json
    provider_hint: str = ""  # preferred provider name

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stop_sequences": list(self.stop_sequences),
            "response_format": self.response_format,
            "provider_hint": self.provider_hint,
        }


@dataclass(frozen=True)
class ReasoningResponse:
    answer: str
    citations: tuple[tuple[str, float], ...] = ()  # (evidence_id, relevance)
    confidence: float = 1.0
    provider: str = ""
    model: str = ""
    usage: UsageMetrics = field(default_factory=UsageMetrics)
    latency_ms: float = 0.0
    warnings: tuple[str, ...] = ()
    unsupported_claims: tuple[str, ...] = ()
    raw_response: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": list(self.citations),
            "confidence": self.confidence,
            "provider": self.provider,
            "model": self.model,
            "usage": self.usage.to_dict(),
            "latency_ms": self.latency_ms,
            "warnings": list(self.warnings),
            "unsupported_claims": list(self.unsupported_claims),
            "raw_response": self.raw_response,
        }


# ── Protocol ─────────────────────────────────────────────────────────

@runtime_checkable
class ReasoningProvider(Protocol):
    """Protocol untuk semua LLM provider."""

    @abstractmethod
    def generate(self, request: ReasoningRequest) -> ReasoningResponse:
        """Generate synchronous response."""
        ...

    @abstractmethod
    def stream(self, request: ReasoningRequest):
        """Stream response chunks. Implement if supports_streaming."""
        raise NotImplementedError

    @abstractmethod
    def health(self) -> bool:
        """Return True if provider is healthy."""
        ...

    @abstractmethod
    def metadata(self) -> ProviderMetadata:
        """Return provider metadata."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Cleanup resources."""
        ...
