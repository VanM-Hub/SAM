"""Knowledge History — riwayat knowledge (Sprint 184).

Phase XVIII — Knowledge Runtime.
Read-only query.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class KnowledgeHistoryEntry:
    """Satu entri riwayat knowledge (immutable)."""
    knowledge_id: str
    action: str
    version: str = "1.0.0"
    external_calls: int = 0


class KnowledgeHistory:
    """Riwayat knowledge. Append + read-only query."""

    def __init__(self) -> None:
        self._entries: List[KnowledgeHistoryEntry] = []

    def record(self, entry: KnowledgeHistoryEntry) -> None:
        self._entries.append(entry)

    def entries(self, knowledge_id: str = None) -> List[KnowledgeHistoryEntry]:
        if knowledge_id is None:
            return list(self._entries)
        return [e for e in self._entries if e.knowledge_id == knowledge_id]

    def count(self) -> int:
        return len(self._entries)
