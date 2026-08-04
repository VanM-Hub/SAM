"""Conversation Execution Builder (Session 02 - Conversation Capability).

AD-S02-001: payload = Execution Context (bukan state Conversation).

- ExecutionRequest tetap DTO generik; TIDAK menambah field.
- Hanya namespace "conversation" yang diisi (kosong lainnya sampai capability aktif).
- Payload serializable, immutable, kontrak lintas layer.
- context identity minimum: conversation_id (dari session_id yang sudah ada),
  request (bukan "intent" - hindari ambigu dgn Session 07), turn_id bila tersedia.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional

from sam.execution_runtime.execution_request import ExecutionRequest


@dataclass(frozen=True)
class ConversationExecutionContext:
    """Context conversation minimum untuk ExecutionRequest preview (immutable)."""
    conversation_id: str
    request: str
    turn_id: Optional[str] = None

    def as_dict(self) -> dict:
        d: Dict[str, object] = {
            "conversation_id": self.conversation_id,
            "request": self.request,
        }
        if self.turn_id:
            d["turn_id"] = self.turn_id
        return d


class ConversationExecutionRequestBuilder:
    """Builder ExecutionRequest(mode='preview') dari konteks conversation.

    Mengisi HANYA payload['conversation'] (AD-S02-001).
    provider_id/operation di-pass dari wiring (dependency injection).
    DTO tidak diubah; ExecutionRuntime tidak diubah; RuntimeService tidak diubah.
    """

    def build(self, context: ConversationExecutionContext,
              provider_id: str,
              operation: str,
              execution_id: str) -> ExecutionRequest:
        if not context.conversation_id or not context.request:
            raise ValueError("conversation_id and request are required")
        payload = {
            "conversation": context.as_dict(),
        }
        return ExecutionRequest(
            execution_id=execution_id,
            provider_id=provider_id,
            operation=operation,
            mode="preview",  # ADR-024 preview-only; bukan execute
            payload=payload,
        )
