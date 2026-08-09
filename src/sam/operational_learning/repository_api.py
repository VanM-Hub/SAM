"""Repository API - WP-07 (MISSION-4.3 / IP-4.3-001).

Antarmuka standar untuk mengakses Experience Repository. API bersifat
read-only, konsisten, query deterministik, siap diintegrasikan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from .experience_repository import ExperienceRepository
from .history import HistoryStore


@dataclass(frozen=True)
class QueryResult:
    """Hasil query (deterministik)."""

    count: int
    items: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"count": self.count, "items": list(self.items)}


class ExperienceQueryAPI:
    """Query experience (read-only)."""

    def __init__(self, repository: ExperienceRepository) -> None:
        self._repo = repository

    def get(self, experience_id: str) -> Optional[Dict[str, Any]]:
        exp = self._repo.get(experience_id)
        return exp.as_dict() if exp else None

    def by_classification(self, classification: str) -> QueryResult:
        items = self._repo.search(classification=classification)
        return QueryResult(
            count=len(items), items=tuple(e.as_dict() for e in items)
        )

    def all(self) -> QueryResult:
        items = self._repo.all()
        return QueryResult(
            count=len(items), items=tuple(e.as_dict() for e in items)
        )


class HistoryQueryAPI:
    """Query history (read-only)."""

    def __init__(self, store: HistoryStore) -> None:
        self._store = store

    def search(
        self, kind: Optional[str] = None, query: str = ""
    ) -> QueryResult:
        items = self._store.search(kind=kind, query=query)
        return QueryResult(
            count=len(items), items=tuple(r.as_dict() for r in items)
        )


class StatisticsAPI:
    """Statistik repository (read-only)."""

    def __init__(self, repository: ExperienceRepository) -> None:
        self._repo = repository

    def statistics(self) -> Dict[str, Any]:
        return self._repo.statistics().as_dict()


class RepositoryAPI:
    """Facade read-only untuk Experience Repository."""

    def __init__(
        self,
        *,
        repository: ExperienceRepository,
        history: HistoryStore,
    ) -> None:
        self._repo = repository
        self._history = history
        self.experiences = ExperienceQueryAPI(repository)
        self.history = HistoryQueryAPI(history)
        self.statistics = StatisticsAPI(repository)

    def metadata(self) -> Dict[str, Any]:
        return self._repo.metadata().as_dict()

    def audit(self) -> Dict[str, Any]:
        return self._repo.audit_report()
