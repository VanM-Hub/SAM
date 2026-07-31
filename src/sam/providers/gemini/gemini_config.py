"""Gemini Provider Config — konfigurasi provider Gemini (Sprint 232).

Preview-only. API key placeholder; tidak dipakai di preview. Immutable.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple


DEFAULT_GEMINI_MODELS: Tuple[str, ...] = (
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
)


@dataclass(frozen=True)
class GeminiProviderConfig:
    """Konfigurasi Gemini (immutable, preview-first)."""
    provider_id: str = "gemini"
    api_key: str = ""
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    models: Tuple[str, ...] = DEFAULT_GEMINI_MODELS
    default_model: str = "gemini-2.5-flash"
    preview_only: bool = True
    external_calls: int = 0

    def supports_model(self, model: str) -> bool:
        return model in self.models

    def resolve_model(self, requested: str) -> str:
        if requested and requested in self.models:
            return requested
        return self.default_model
