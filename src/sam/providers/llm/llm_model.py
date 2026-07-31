"""LLM Model — representasi generik model LLM (Sprint 229)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass(frozen=True)
class LLMModelCapability:
    """Kapabilitas teknis sebuah model (immutable)."""
    context_window: int = 8192
    max_output_tokens: int = 4096
    supports_tools: bool = False
    supports_vision: bool = False
    supports_json: bool = True


@dataclass(frozen=True)
class LLMModel:
    """Deskripsi model generik (immutable)."""
    model_id: str
    provider_id: str
    display_name: str = ""
    capability: LLMModelCapability = field(default_factory=LLMModelCapability)
    preview_only: bool = True
    external_calls: int = 0

    @property
    def key(self) -> str:
        return f"{self.provider_id}:{self.model_id}"
