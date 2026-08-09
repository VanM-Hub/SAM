"""Experience Context - WP-34 (MISSION-5.1 / IP-5.1-004).

Menghubungkan reasoning dengan pengalaman operasional yang telah disimpan.
Experience memiliki provenance dan timestamp.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class ExperienceEntry:
    """Satu pengalaman operasional tersimpan."""

    experience_id: str
    kind: str  # investigation | execution | verification
    summary: str
    outcome: str
    timestamp: str = ""
    source: str = ""
    relevance: float = 0.0

    def as_dict(self) -> dict:
        return {
            "experience_id": self.experience_id,
            "kind": self.kind,
            "summary": self.summary,
            "outcome": self.outcome,
            "timestamp": self.timestamp,
            "source": self.source,
            "relevance": self.relevance,
        }


class ExperienceContextProvider:
    """Retrieval pengalaman operasional untuk reasoning."""

    def __init__(self) -> None:
        self._store: Dict[str, ExperienceEntry] = {}

    def store(self, entry: ExperienceEntry) -> None:
        self._store[entry.experience_id] = entry

    def retrieve(self, experience_ids: Tuple[str, ...]) -> Tuple[ExperienceEntry, ...]:
        return tuple(self._store.get(eid) for eid in experience_ids if eid in self._store)

    def discover_similar(self, kind: str, limit: int = 3) -> Tuple[ExperienceEntry, ...]:
        similar = [e for e in self._store.values() if e.kind == kind]
        similar.sort(key=lambda e: e.relevance, reverse=True)
        return tuple(similar[:limit])

    def all(self) -> Tuple[ExperienceEntry, ...]:
        return tuple(self._store.values())
