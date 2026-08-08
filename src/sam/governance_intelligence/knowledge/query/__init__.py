"""WP-03 — Knowledge Query API (IP-3.1-001).

Deterministic query surface over repositories. Exposes:

    find()      : exact lookup by key/id.
    search()    : substring match across title/content.
    lookup()    : normalized match by facet or concept (case-insensitive).
    reference() : locate items by their declared source/reference.

Outputs are immutable DTOs (``QueryResult``). No AI, no ranking heuristics —
matches are exact/exclusion based and returned in stable (source) order.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.knowledge.repository import QueryOnlyRepository


@dataclass(frozen=True)
class QueryResult:
    """Immutable DTO produced by the Query API (WP-03)."""

    query: str
    repository: str
    items: List[KnowledgeItem] = field(default_factory=list)

    def keys(self) -> List[str]:
        return [it.key for it in self.items]

    def size(self) -> int:
        return len(self.items)

    def jsonable(self) -> dict:
        return {
            "query": self.query,
            "repository": self.repository,
            "items": [it.public_dict() for it in self.items],
        }


class KnowledgeQueryAPI:
    """WP-03 implementation. Stateless; operates over any repository."""

    def find(self, repo: QueryOnlyRepository, key: str) -> QueryResult:
        item = repo.by_key(key)
        items = [item] if item else []
        return QueryResult(query=key, repository=repo.__class__.__name__, items=items)

    def search(self, repo: QueryOnlyRepository, term: str) -> QueryResult:
        low = term.lower()
        items = [
            it
            for it in repo.all()
            if low in it.title.lower() or low in it.content.lower()
        ]
        return QueryResult(query=term, repository=repo.__class__.__name__, items=items)

    def lookup(self, repo: QueryOnlyRepository, concept: str) -> QueryResult:
        low = concept.lower().strip()
        items = [
            it
            for it in repo.all()
            if low in it.key.lower()
            or low in it.section.lower()
            or low == str(it.metadata.get("facet", "")).lower()
        ]
        return QueryResult(query=concept, repository=repo.__class__.__name__, items=items)

    def reference(self, repo: QueryOnlyRepository, source: str) -> QueryResult:
        items = [it for it in repo.all() if source in it.source]
        return QueryResult(query=source, repository=repo.__class__.__name__, items=items)
