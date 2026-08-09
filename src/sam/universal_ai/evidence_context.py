"""Evidence Context - WP-32 (MISSION-5.1 / IP-5.1-004).

Mengintegrasikan evidence ke reasoning context. AI tidak menerima evidence yang
kehilangan source reference; setiap evidence dapat ditelusuri ke sumbernya.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class EvidenceContextEntry:
    """Satu evidence dengan provenance lengkap."""

    evidence_id: str
    source_type: str
    source_id: str
    relevance: float = 0.0
    freshness: str = ""
    content: str = ""

    @property
    def has_source(self) -> bool:
        return bool(self.source_type and self.source_id)

    def as_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "relevance": self.relevance,
            "freshness": self.freshness,
            "content": self.content,
            "has_source": self.has_source,
        }


class EvidenceContextProvider:
    """Menyediakan evidence ke reasoning (retrieval/filter/rank)."""

    def __init__(self) -> None:
        self._evidence: Dict[str, EvidenceContextEntry] = {}

    def add(self, entry: EvidenceContextEntry) -> None:
        self._evidence[entry.evidence_id] = entry

    def retrieve(self, evidence_ids: Tuple[str, ...]) -> Tuple[EvidenceContextEntry, ...]:
        found = []
        for eid in evidence_ids:
            entry = self._evidence.get(eid)
            if entry is not None and entry.has_source:
                found.append(entry)
        return tuple(found)

    def retrieve_all(self) -> Tuple[EvidenceContextEntry, ...]:
        return tuple(self._evidence.values())

    def filter_provenance(self, evidence_ids: Tuple[str, ...]) -> Tuple[str, ...]:
        """Hanya kembalikan id evidence yang memiliki source reference."""
        return tuple(e.evidence_id for e in self.retrieve(evidence_ids))

    def rank(self, evidence_ids: Tuple[str, ...], limit: int = 5) -> Tuple[str, ...]:
        ranked = sorted(
            self.retrieve(evidence_ids), key=lambda e: e.relevance, reverse=True
        )
        return tuple(e.evidence_id for e in ranked[:limit])
