"""Conversation Artifact Bridge — 5 read-only queries (Sprint 220)."""
from __future__ import annotations

from .artifact_descriptor import ArtifactDescriptor
from .artifact_registry import ArtifactRegistry


class ConversationArtifactBridge:
    """Bridge conversation — 5 query read-only fondasi artifact."""

    def __init__(self, registry: ArtifactRegistry) -> None:
        self._registry = registry

    def query_1_descriptors(self):
        return self._registry.all()

    def query_2_count(self) -> int:
        return self._registry.count()

    def query_3_names(self):
        return self._registry.names()

    def query_4_lookup(self, name: str):
        return self._registry.lookup(name)

    def query_5_metadata(self) -> dict:
        return {"version": "23.0.0", "runtime": "artifact", "preview_only": True}
