"""Chat Model — representasi model chat (Sprint 241).

Program B — Model Runtime Integration.
Preview only; mendukung peran system|user|assistant|tool.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from ..model_runtime.model_message import ModelMessage


@dataclass(frozen=True)
class ChatModel:
    """Model chat (immutable). Read-only, preview-only."""
    chat_id: str
    name: str
    supports_system: bool = True
    supports_tool: bool = True
    max_context_tokens: Optional[int] = None
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "chat_id": self.chat_id,
            "name": self.name,
            "supports_system": self.supports_system,
            "supports_tool": self.supports_tool,
            "max_context_tokens": self.max_context_tokens,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }
