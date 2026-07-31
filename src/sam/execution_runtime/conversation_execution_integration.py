"""Conversation Execution Integration (Sprint 259).

Program C - Real Execution Runtime.
Read-only bridge: integrasi execution pada konteks percakapan.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .execution_integration import ExecutionIntegration, ExecutionIntegrationResult
from .execution_descriptor import ExecutionDescriptor
from .execution_request import ExecutionRequest


@dataclass(frozen=True)
class ConversationExecutionIntegrationView:
    """View integrasi pada percakapan (immutable)."""
    conversation_id: str
    integration: ExecutionIntegrationResult
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {"conversation_id": self.conversation_id,
                "integration": self.integration.as_dict(),
                "preview_only": self.preview_only,
                "external_calls": self.external_calls}


class ConversationExecutionIntegration:
    """Bridge execution integration <-> conversation. Read-only."""

    def __init__(self, integration: ExecutionIntegration | None = None) -> None:
        self._integration = integration or ExecutionIntegration()

    def run(self, conversation_id: str, descriptor: ExecutionDescriptor,
            request: ExecutionRequest) -> ConversationExecutionIntegrationView:
        result = self._integration.run(descriptor, request)
        return ConversationExecutionIntegrationView(
            conversation_id=conversation_id,
            integration=result,
            preview_only=result.preview_only,
            external_calls=result.external_calls,
        )
