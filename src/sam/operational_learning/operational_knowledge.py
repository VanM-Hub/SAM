"""Operational Knowledge + Knowledge Index - WP-15/16 (MISSION-4.3 / IP-4.3-002).

Mengubah pengalaman menjadi pengetahuan operasional yang terindeks.
Seluruh knowledge memiliki evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from .case_repository import Case
from .lesson_extraction import Lesson


@dataclass(frozen=True)
class KnowledgeEntry:
    """Satu entri pengetahuan operasional."""

    knowledge_id: str
    title: str
    content: str
    category: str = "general"
    evidence_ids: Tuple[str, ...] = field(default_factory=tuple)
    source_case_ids: Tuple[str, ...] = field(default_factory=tuple)
    confidence: float = 0.0

    def as_dict(self) -> dict:
        return {
            "knowledge_id": self.knowledge_id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "evidence_ids": list(self.evidence_ids),
            "source_case_ids": list(self.source_case_ids),
            "confidence": self.confidence,
        }


class KnowledgeIndex:
    """Index pengetahuan (deterministik, by-query)."""

    def __init__(self) -> None:
        self._entries: Dict[str, KnowledgeEntry] = {}

    def add(self, entry: KnowledgeEntry) -> None:
        self._entries[entry.knowledge_id] = entry

    def get(self, knowledge_id: str) -> Optional[KnowledgeEntry]:
        return self._entries.get(knowledge_id)

    def all(self) -> Tuple[KnowledgeEntry, ...]:
        return tuple(self._entries.values())

    def count(self) -> int:
        return len(self._entries)

    def search(self, query: str = "") -> Tuple[KnowledgeEntry, ...]:
        entries = self.all()
        if not query:
            return entries
        q = query.lower()
        return tuple(
            e
            for e in entries
            if q in e.title.lower() or q in e.content.lower()
        )


class OperationalKnowledge:
    """Knowledge base operasional (dibangun dari kasus & pelajaran)."""

    def __init__(self, index: Optional[KnowledgeIndex] = None) -> None:
        self._index = index or KnowledgeIndex()

    @property
    def index(self) -> KnowledgeIndex:
        return self._index

    def build_from_case(self, case: Case, lesson: Lesson) -> KnowledgeEntry:
        entry = KnowledgeEntry(
            knowledge_id=case.case_id,
            title=f"Knowledge: {case.title}",
            content=lesson.content,
            category=lesson.category,
            evidence_ids=case.evidence_ids,
            source_case_ids=(case.case_id,),
            confidence=self._confidence(case, lesson),
        )
        self._index.add(entry)
        return entry

    @staticmethod
    def _confidence(case: Case, lesson: Lesson) -> float:
        base = 0.3
        if case.outcome:
            base += 0.4
        if lesson.source_evidence:
            base += 0.2
        return round(min(1.0, base), 3)
