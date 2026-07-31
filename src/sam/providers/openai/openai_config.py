"""OpenAI Provider Config — konfigurasi provider OpenAI (Sprint 230).

Preview-only: default tidak ada network call. API key disimpan sebagai
placeholder (tidak pernah dipakai di mode preview). Immutable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple


DEFAULT_OPENAI_MODELS: Tuple[str, ...] = (
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-3.5-turbo",
)


@dataclass(frozen=True)
class OpenAIProviderConfig:
    """Konfigurasi OpenAI (immutable, preview-first)."""
    provider_id: str = "openai"
    api_key: str = ""  # placeholder; tidak dipakai di preview
    base_url: str = "https://api.openai.com/v1"
    models: Tuple[str, ...] = DEFAULT_OPENAI_MODELS
    default_model: str = "gpt-4o-mini"
    preview_only: bool = True
    external_calls: int = 0

    def supports_model(self, model: str) -> bool:
        return model in self.models

    def resolve_model(self, requested: str) -> str:
        if requested and requested in self.models:
            return requested
        return self.default_model
