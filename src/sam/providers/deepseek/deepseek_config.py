"""DeepSeek Provider Config — konfigurasi provider DeepSeek (Sprint 233).

Preview-only. API key placeholder. Immutable.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple


DEFAULT_DEEPSEEK_MODELS: Tuple[str, ...] = (
    "deepseek-chat",
    "deepseek-reasoner",
    "deepseek-v4-flash",
    "deepseek-v4-pro",
)


@dataclass(frozen=True)
class DeepSeekProviderConfig:
    """Konfigurasi DeepSeek (immutable, preview-first)."""
    provider_id: str = "deepseek"
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    models: Tuple[str, ...] = DEFAULT_DEEPSEEK_MODELS
    default_model: str = "deepseek-chat"
    preview_only: bool = True
    external_calls: int = 0

    def supports_model(self, model: str) -> bool:
        return model in self.models

    def resolve_model(self, requested: str) -> str:
        if requested and requested in self.models:
            return requested
        return self.default_model
