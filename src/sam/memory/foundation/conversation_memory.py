"""Conversation Memory Bridge — 5 query read-only (Sprint 172)."""
from __future__ import annotations

from .memory_registry import MemoryRegistry


class ConversationMemoryBridge:
    """Bridge conversation — 5 query read-only memori."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry

    def query_1_summary(self) -> dict:
        """Query 1 — ringkasan registry."""
        s = self._registry.summary()
        return {"total": s.total, "by_category": s.by_category}

    def query_2_list(self) -> list:
        """Query 2 — daftar id memori."""
        return self._registry.list_ids()

    def query_3_descriptor(self, memory_id: str) -> str:
        """Query 3 — nama descriptor."""
        d = self._registry.find(memory_id)
        return d.name if d else f"memory {memory_id} not found"

    def query_4_metadata(self, memory_id: str) -> dict:
        """Query 4 — metadata."""
        m = self._registry.get_metadata(memory_id)
        if m is None:
            return {}
        return {"author": m.author, "tags": m.tags}

    def query_5_capability(self, memory_id: str) -> list:
        """Query 5 — id kapabilitas."""
        return [c.capability_id for c in self._registry.get_capabilities(memory_id)]
