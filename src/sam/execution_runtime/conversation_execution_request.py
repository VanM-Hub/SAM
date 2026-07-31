"""Conversation Execution Request (Sprint 251).

Program C - Real Execution Runtime.
Read-only bridge: konversi context percakapan -> request eksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass

from .execution_request import ExecutionRequest


@dataclass(frozen=True)
class ConversationExecutionRequestView:
    """View request pada konteks percakapan (immutable)."""
    conversation_id: str
    execution_id: str = ""
    provider_id: str = ""
    approved: bool = False
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "execution_id": self.execution_id,
            "provider_id": self.provider_id,
            "approved": self.approved,
            "external_calls": self.external_calls,
        }


class ConversationExecutionRequest:
    """Bridge execution request <-> conversation. Read-only."""

    def view(self, conversation_id: str, request: ExecutionRequest) -> ConversationExecutionRequestView:
        return ConversationExecutionRequestView(
            conversation_id=conversation_id,
            execution_id=request.execution_id,
            provider_id=request.provider_id,
            approved=request.approved,
            external_calls=0,  # preview-only view
        )
