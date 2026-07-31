"""Provider Selector — pemilih provider (Sprint 247).

Program B — Model Runtime Integration.
Mapping: OpenAI, Anthropic, Gemini, DeepSeek, Ollama. Belum network.
Deterministik, read-only, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .provider_mapping import ProviderMapping


@dataclass(frozen=True)
class ProviderSelection:
    """Hasil seleksi provider (immutable)."""
    selection_id: str
    provider: str = "openai"
    provider_model: str = ""
    reason: str = ""
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "selection_id": self.selection_id,
            "provider": self.provider,
            "provider_model": self.provider_model,
            "reason": self.reason,
            "external_calls": self.external_calls,
        }


class ProviderSelector:
    """Pemilih provider. Deterministik, no-network, read-only."""

    KNOWN = ("openai", "anthropic", "gemini", "deepseek", "ollama")

    def select(self, mapping: ProviderMapping) -> ProviderSelection:
        provider = mapping.provider if mapping.provider in self.KNOWN else "openai"
        reason = "mapped" if mapping.provider in self.KNOWN else "fallback-default"
        return ProviderSelection(
            selection_id=f"sel-{mapping.mapping_id}",
            provider=provider,
            provider_model=mapping.provider_model or mapping.model_name,
            reason=reason,
            external_calls=0,
        )
