"""Conversation Mapping — bridge conversation <-> provider mapping (Sprint 247).

Program B — Model Runtime Integration.
Read-only bridge; mapping provider, belum network.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .provider_mapping import ProviderMapping
from .provider_selector import ProviderSelector, ProviderSelection


@dataclass(frozen=True)
class ConversationMappingResult:
    """Hasil mapping pada konteks percakapan (immutable)."""
    conversation_id: str
    mapping: ProviderMapping
    selection: ProviderSelection
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "mapping": self.mapping.as_dict(),
            "selection": self.selection.as_dict(),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ConversationMapping:
    """Bridge conversation <-> provider mapping. Read-only, no-network."""

    def __init__(self, selector: ProviderSelector | None = None) -> None:
        self._selector = selector or ProviderSelector()

    def resolve(self, conversation_id: str, mapping: ProviderMapping) -> ConversationMappingResult:
        selection = self._selector.select(mapping)
        return ConversationMappingResult(
            conversation_id=conversation_id,
            mapping=mapping,
            selection=selection,
            preview_only=True,
            external_calls=0,
        )
