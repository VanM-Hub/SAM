"""Ollama Provider Config — konfigurasi provider Ollama (Sprint 234).

Ollama adalah model lokal. Tetap preview-only: tidak ada network call di
mode preview. Immutable.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple


DEFAULT_OLLAMA_MODELS: Tuple[str, ...] = (
    "llama3.3-70b",
    "llama3.2",
    "gemma3:1b",
    "qwen3",
)


@dataclass(frozen=True)
class OllamaProviderConfig:
    """Konfigurasi Ollama (immutable, preview-first)."""
    provider_id: str = "ollama"
    base_url: str = "http://localhost:11434"
    models: Tuple[str, ...] = DEFAULT_OLLAMA_MODELS
    default_model: str = "llama3.3-70b"
    preview_only: bool = True
    external_calls: int = 0

    def supports_model(self, model: str) -> bool:
        return model in self.models

    def resolve_model(self, requested: str) -> str:
        if requested and requested in self.models:
            return requested
        return self.default_model
