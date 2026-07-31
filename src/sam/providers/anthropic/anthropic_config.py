"""Anthropic Provider Config — konfigurasi provider Anthropic (Sprint 231).

Preview-only: default tidak ada network call. API key placeholder.
Immutable.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple


DEFAULT_ANTHROPIC_MODELS: Tuple[str, ...] = (
    "claude-opus-4-6",
    "claude-opus-4-7",
    "claude-opus-4-8",
    "claude-sonnet-4-6",
)


@dataclass(frozen=True)
class AnthropicProviderConfig:
    """Konfigurasi Anthropic (immutable, preview-first)."""
    provider_id: str = "anthropic"
    api_key: str = ""
    base_url: str = "https://api.anthropic.com/v1"
    models: Tuple[str, ...] = DEFAULT_ANTHROPIC_MODELS
    default_model: str = "claude-sonnet-4-6"
    preview_only: bool = True
    external_calls: int = 0

    def supports_model(self, model: str) -> bool:
        return model in self.models

    def resolve_model(self, requested: str) -> str:
        if requested and requested in self.models:
            return requested
        return self.default_model
