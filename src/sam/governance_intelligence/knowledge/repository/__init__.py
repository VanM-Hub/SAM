"""WP-02 — repository interfaces (IP-3.1-001).

Repository layer converts indexes into queryable repositories. Per directive:

  *  knowledge/repository/  — "Tidak boleh ada logic." ("No logic allowed.")
  *  Repository hanya query. ("Repository only queries.")

So each repository here is a thin, read-only query surface over an index:
it may FILTER / look up / project, but must NOT transform, reword, or reason.
Logic lives in the Reasoning layer (WP-05) and Analysis layer (WP-07..09).
"""

from __future__ import annotations

from typing import List, Optional

from sam.governance_intelligence.knowledge.models import KnowledgeIndex, KnowledgeItem


class QueryOnlyRepository:
    """Base for all repositories. Query-only, deterministic, logic-free."""

    def __init__(self, index: KnowledgeIndex) -> None:
        self._index = index

    def all(self) -> List[KnowledgeItem]:
        return self._index.all()

    def by_key(self, key: str) -> Optional[KnowledgeItem]:
        return self._index.by_key(key)

    def by_section(self, section: str) -> List[KnowledgeItem]:
        return [it for it in self._index.all() if it.section == section]

    def by_kind(self, kind: str) -> List[KnowledgeItem]:
        return self._index.by_kind(kind)

    def size(self) -> int:
        return self._index.size()

    def index(self) -> KnowledgeIndex:
        return self._index


class MissionRepository(QueryOnlyRepository):
    """Query surface over the Mission index (WP-01)."""


class ADRRepository(QueryOnlyRepository):
    """Query surface over accepted ADRs (WP-01)."""

    def accepted(self) -> List[KnowledgeItem]:
        return [it for it in self._index.all() if it.metadata.get("status", "Accepted") == "Accepted"]


class PolicyRepository(QueryOnlyRepository):
    """Query surface over Policy items (from Governance index)."""


class RuntimeRepository(QueryOnlyRepository):
    """Query surface over Runtime items (from Governance index)."""


class EvidenceRepository(QueryOnlyRepository):
    """Query surface over evidence records.

    Evidence is stored separately from normative knowledge (WP-04). Each
    evidence item is keyed by the claim/question it supports; the resolver
    (WP-04/evidence/resolver) queries here for traceability.
    """

    def by_claim(self, claim_key: str) -> List[KnowledgeItem]:
        return [it for it in self._index.all() if it.key.startswith(f"evidence.{claim_key}")]
