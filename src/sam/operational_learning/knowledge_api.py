"""Knowledge API - WP-17 (MISSION-4.3 / IP-4.3-002).

Antarmuka standar untuk mengakses Operational Knowledge. API read-only,
query deterministik, siap diintegrasikan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from .case_repository import CaseRepository
from .operational_knowledge import KnowledgeIndex


@dataclass(frozen=True)
class KnowledgeQueryResult:
    """Hasil query knowledge (deterministik)."""

    count: int
    items: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"count": self.count, "items": list(self.items)}


class KnowledgeQueryAPI:
    """Query knowledge (read-only)."""

    def __init__(self, index: KnowledgeIndex) -> None:
        self._index = index

    def search(self, query: str = "") -> KnowledgeQueryResult:
        items = self._index.search(query)
        return KnowledgeQueryResult(
            count=len(items), items=tuple(e.as_dict() for e in items)
        )

    def get(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        entry = self._index.get(knowledge_id)
        return entry.as_dict() if entry else None

    def all(self) -> KnowledgeQueryResult:
        items = self._index.all()
        return KnowledgeQueryResult(
            count=len(items), items=tuple(e.as_dict() for e in items)
        )


class CaseQueryAPI:
    """Query kasus (read-only)."""

    def __init__(self, repository: CaseRepository) -> None:
        self._repo = repository

    def search(self, query: str = "") -> KnowledgeQueryResult:
        cases = self._repo.search(query)
        return KnowledgeQueryResult(
            count=len(cases), items=tuple(c.as_dict() for c in cases)
        )

    def get(self, case_id: str) -> Optional[Dict[str, Any]]:
        case = self._repo.get(case_id)
        return case.as_dict() if case else None


class KnowledgeAPI:
    """Facade read-only untuk Operational Knowledge."""

    def __init__(
        self,
        *,
        knowledge: KnowledgeIndex,
        cases: CaseRepository,
    ) -> None:
        self._knowledge = knowledge
        self._cases = cases
        self.knowledge = KnowledgeQueryAPI(knowledge)
        self.cases = CaseQueryAPI(cases)

    def knowledge_count(self) -> int:
        return self._knowledge.count()

    def case_count(self) -> int:
        return self._cases.count()
