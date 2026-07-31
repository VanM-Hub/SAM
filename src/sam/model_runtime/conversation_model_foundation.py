"""Conversation Model Foundation — bridge conversation <-> model (Sprint 239).

Program B — Model Runtime Integration.
Read-only bridge; external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .model_descriptor import ModelDescriptor
from .model_registry import ModelRegistry


@dataclass(frozen=True)
class ConversationModelBinding:
    """Representasi immutable binding conversation ke sebuah model."""
    conversation_id: str
    model_id: str
    role: str = "assistant"
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "model_id": self.model_id,
            "role": self.role,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ConversationModelFoundation:
    """Bridge conversation <-> model foundation. Read-only."""

    def __init__(self, registry: ModelRegistry | None = None) -> None:
        self._registry = registry or ModelRegistry()

    def bind(self, conversation_id: str, model_id: str, role: str = "assistant") -> ConversationModelBinding:
        if not self._registry.exists(model_id):
            raise ValueError(f"model not found: {model_id}")
        return ConversationModelBinding(
            conversation_id=conversation_id,
            model_id=model_id,
            role=role,
            preview_only=True,
            external_calls=0,
        )

    def models_for(self, conversation_id: str) -> List[ModelDescriptor]:
        return list(self._registry.all())

    def has_model(self, model_id: str) -> bool:
        return self._registry.exists(model_id)
