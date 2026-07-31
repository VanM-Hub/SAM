"""Conversation Context Bridge — query read-only (Sprint 189)."""
from __future__ import annotations

from .cognitive_context import CognitiveContext
from .cognitive_snapshot import CognitiveSnapshot
from .cognitive_scope import CognitiveScope
from .cognitive_reference import CognitiveReference


class ConversationContextBridge:
    """Bridge conversation — query konteks kognitif read-only."""

    def build_context(self, cognitive_id: str, scope: str = "mission") -> CognitiveContext:
        return CognitiveContext(cognitive_id=cognitive_id, scope=scope)

    def build_snapshot(self, snapshot_id: str, context: CognitiveContext) -> CognitiveSnapshot:
        return CognitiveSnapshot(snapshot_id=snapshot_id, context=context)

    def summary(self, context: CognitiveContext) -> dict:
        return {
            "cognitive_id": context.cognitive_id,
            "scope": context.scope,
            "entry_count": context.entry_count(),
        }
