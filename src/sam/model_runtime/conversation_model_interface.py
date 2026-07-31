"""Conversation Model Interface — bridge conversation <-> model interface (Sprint 240).

Program B — Model Runtime Integration.
Read-only bridge; tidak mengenal provider.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .model_request import ModelRequest
from .model_response import ModelResponse
from .model_message import ModelMessage
from .model_validator import ModelValidator, ModelValidationResult


@dataclass(frozen=True)
class ConversationTurn:
    """Satu giliran percakapan (immutable)."""
    turn_id: str
    request: ModelRequest
    response: ModelResponse
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "turn_id": self.turn_id,
            "request": self.request.as_dict(),
            "response": self.response.as_dict(),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ConversationModelInterface:
    """Bridge conversation <-> model interface. Read-only, no provider."""

    def __init__(self, validator: ModelValidator | None = None) -> None:
        self._validator = validator or ModelValidator()
        self._turns: List[ConversationTurn] = []

    def validate(self, request: ModelRequest) -> ModelValidationResult:
        return self._validator.validate_request(request)

    def record(self, turn: ConversationTurn) -> None:
        # in-memory log; tidak ada write eksternal
        self._turns.append(turn)

    def turns(self) -> List[ConversationTurn]:
        return list(self._turns)

    def count(self) -> int:
        return len(self._turns)
