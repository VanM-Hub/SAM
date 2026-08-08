"""WP-01 — base Knowledge Model primitives (IP-3.1-001).

These are the smallest immutable building blocks used by every index in
WP-01..03. Keep them deterministic and free of domain logic. Specialized
field meanings are declared by the index that creates them; the primitives
themselves are generic.

All DTOs are immutable (pydantic v2 frozen) so a knowledge index can be
shared/cached/compared safely and never silently mutated.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgeItem(BaseModel):
    """One atomic, traceable unit of normative knowledge.

    Fields
    ------
    key        : stable identifier (e.g. 'mission.objective')
    kind       : document kind the item came from ('mission','adr',...)
    source     : file path or URL the item was parsed from (traceability)
    section    : original section/heading (traceability)
    title      : human title of the item
    content    : exact source text (never reworded)
    signature  : stable content hash for change detection
    metadata   : optional extra fields (level, status, etc.)
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: str(uuid4()))
    key: str
    kind: str
    source: str
    section: str = ""
    title: str
    content: str
    signature: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now_utc)

    def public_dict(self) -> Dict[str, Any]:
        """Serializable projection without mutable internals."""
        return {
            "key": self.key,
            "kind": self.kind,
            "source": self.source,
            "section": self.section,
            "title": self.title,
            "content": self.content,
            "signature": self.signature,
            "metadata": {k: v for k, v in self.metadata.items()},
        }


class KnowledgeIndex(BaseModel):
    """A named collection of immutable knowledge items (WP-01 output).

    The index supports deterministic lookups by key and by kind. It DOES NOT
    implement AI search — matching is exact/exclusion based. It is itself
    immutable and hashable for snapshot comparison.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    items: List[KnowledgeItem] = Field(default_factory=list)

    def by_key(self, key: str) -> Optional[KnowledgeItem]:
        for it in reversed(self.items):
            if it.key == key:
                return it
        return None

    def by_kind(self, kind: str) -> List[KnowledgeItem]:
        return [it for it in self.items if it.kind == kind]

    def all(self) -> List[KnowledgeItem]:
        return list(self.items)

    def size(self) -> int:
        return len(self.items)

    def signatures(self) -> Dict[str, str]:
        return {it.key: it.signature for it in self.items}
