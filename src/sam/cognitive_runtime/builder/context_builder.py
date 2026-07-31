"""Context Builder — membangun CognitiveContext (Sprint 190)."""
from __future__ import annotations
from typing import List

from ..context.cognitive_context import CognitiveContext


class ContextBuilder:
    """Builder konteks. Menyusun DTO saja, tanpa reasoning/inferensi."""

    def build(self, cognitive_id: str, scope: str = "mission",
              entries: List[str] = None) -> CognitiveContext:
        return CognitiveContext(
            cognitive_id=cognitive_id, scope=scope, entries=list(entries or []),
        )

    def add_entry(self, context: CognitiveContext, entry: str) -> CognitiveContext:
        return CognitiveContext(
            cognitive_id=context.cognitive_id, scope=context.scope,
            entries=list(context.entries) + [entry],
            metadata=dict(context.metadata),
        )
