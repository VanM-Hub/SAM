"""Conversation Integration — bridge conversation <-> model integration (Sprint 249).

Program B — Model Runtime Integration.
Read-only bridge ke pipeline akhir. Preview-only, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .model_integration import ModelIntegration, ModelIntegrationResult
from .model_descriptor import ModelDescriptor
from .model_request import ModelRequest


@dataclass(frozen=True)
class ConversationIntegrationResult:
    """Hasil integrasi pada konteks percakapan (immutable)."""
    conversation_id: str
    integration: ModelIntegrationResult
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "integration": self.integration.as_dict(),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ConversationIntegration:
    """Bridge conversation <-> model integration. Read-only."""

    def __init__(self, integration: ModelIntegration | None = None) -> None:
        self._integration = integration or ModelIntegration()

    def run(self, conversation_id: str, descriptor: ModelDescriptor, request: ModelRequest) -> ConversationIntegrationResult:
        result = self._integration.run(descriptor, request)
        return ConversationIntegrationResult(
            conversation_id=conversation_id,
            integration=result,
            preview_only=True,
            external_calls=0,
        )
