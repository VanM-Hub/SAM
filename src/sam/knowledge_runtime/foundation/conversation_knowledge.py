"""Conversation Knowledge Bridge — 5 query read-only (Sprint 180)."""
from __future__ import annotations

from .knowledge_registry import KnowledgeRegistry


class ConversationKnowledgeBridge:
    """Bridge conversation — 5 query read-only knowledge."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry

    def query_1_summary(self) -> dict:
        """Query 1 — ringkasan registry."""
        s = self._registry.summary()
        return {"total": s.total, "by_category": s.by_category}

    def query_2_list(self) -> list:
        """Query 2 — daftar id knowledge."""
        return self._registry.list_ids()

    def query_3_descriptor(self, knowledge_id: str) -> str:
        """Query 3 — nama descriptor."""
        d = self._registry.find(knowledge_id)
        return d.name if d else f"knowledge {knowledge_id} not found"

    def query_4_metadata(self, knowledge_id: str) -> dict:
        """Query 4 — metadata."""
        m = self._registry.get_metadata(knowledge_id)
        if m is None:
            return {}
        return {"author": m.author, "tags": m.tags}

    def query_5_capability(self, knowledge_id: str) -> list:
        """Query 5 — id kapabilitas."""
        return [c.capability_id for c in self._registry.get_capabilities(knowledge_id)]
