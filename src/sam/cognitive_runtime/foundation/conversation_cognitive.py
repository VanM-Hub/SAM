"""Conversation Cognitive Bridge — query read-only (Sprint 188)."""
from __future__ import annotations

from .cognitive_registry import CognitiveRegistry


class ConversationCognitiveBridge:
    """Bridge conversation — status kognitif read-only."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry

    def summary(self) -> dict:
        return {
            "total_Cognitive": self._registry.count(),
            "preview_only": True,
        }

    def status(self, cognitive_id: str) -> str:
        return "registered" if self._registry.exists(cognitive_id) else "missing"
