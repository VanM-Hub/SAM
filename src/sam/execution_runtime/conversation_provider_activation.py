"""Conversation Provider Activation (Sprint 260).

Program C - Real Execution Runtime.
Read-only bridge: status aktivasi provider pada konteks percakapan.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .provider_activation import ProviderActivationExecutor
from ..providers.execution.provider_executor import PROVIDER_ENV


@dataclass(frozen=True)
class ConversationProviderActivationView:
    """View aktivasi provider pada percakapan (immutable)."""
    conversation_id: str
    available_providers: int = 0
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {"conversation_id": self.conversation_id,
                "available_providers": self.available_providers,
                "external_calls": self.external_calls}


class ConversationProviderActivation:
    """Bridge provider activation <-> conversation. Read-only."""

    def __init__(self, executor: ProviderActivationExecutor | None = None) -> None:
        self._executor = executor or ProviderActivationExecutor()

    def view(self, conversation_id: str) -> ConversationProviderActivationView:
        available = sum(1 for pid in PROVIDER_ENV
                        if self._executor._real.available(pid))
        return ConversationProviderActivationView(
            conversation_id=conversation_id,
            available_providers=available,
            external_calls=0,
        )
