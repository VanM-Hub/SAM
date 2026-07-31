"""Provider Mapping — pemetaan model <-> provider (Sprint 247).

Program B — Model Runtime Integration.
Mapping: OpenAI, Anthropic, Gemini, DeepSeek, Ollama. Belum network.
Immutable, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class ProviderMapping:
    """Pemetaan model -> provider (immutable). Tidak ada network call."""
    mapping_id: str
    model_name: str
    provider: str = "openai"  # openai | anthropic | gemini | deepseek | ollama
    provider_model: str = ""
    model_type: str = "chat"
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "mapping_id": self.mapping_id,
            "model_name": self.model_name,
            "provider": self.provider,
            "provider_model": self.provider_model,
            "model_type": self.model_type,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }
