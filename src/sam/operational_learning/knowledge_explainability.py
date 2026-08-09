"""Knowledge Explainability - WP-18 (MISSION-4.3 / IP-4.3-002).

Menjelaskan asal-usul setiap pengetahuan: kasus sumber, evidence, dan
pelajaran yang membentuknya.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .case_repository import Case
from .operational_knowledge import KnowledgeEntry


@dataclass(frozen=True)
class KnowledgeTrace:
    """Trace asal-usul sebuah knowledge."""

    knowledge_id: str
    source_case_ids: Tuple[str, ...] = field(default_factory=tuple)
    evidence_ids: Tuple[str, ...] = field(default_factory=tuple)
    lesson_content: str = ""

    def as_dict(self) -> dict:
        return {
            "knowledge_id": self.knowledge_id,
            "source_case_ids": list(self.source_case_ids),
            "evidence_ids": list(self.evidence_ids),
            "lesson_content": self.lesson_content,
        }


@dataclass(frozen=True)
class KnowledgeExplanation:
    """Penjelasan penuh sebuah knowledge."""

    knowledge: KnowledgeEntry
    trace: KnowledgeTrace

    def as_dict(self) -> dict:
        return {
            "knowledge": self.knowledge.as_dict(),
            "trace": self.trace.as_dict(),
        }


class KnowledgeExplainer:
    """Menjelaskan knowledge (read-only)."""

    def explain(self, entry: KnowledgeEntry, cases: Tuple[Case, ...]) -> KnowledgeExplanation:
        by_id = {c.case_id: c for c in cases}
        lesson_content = ""
        if entry.source_case_ids:
            first = by_id.get(entry.source_case_ids[0])
            if first is not None:
                lesson_content = f"Derived from case: {first.title}"
        trace = KnowledgeTrace(
            knowledge_id=entry.knowledge_id,
            source_case_ids=entry.source_case_ids,
            evidence_ids=entry.evidence_ids,
            lesson_content=lesson_content,
        )
        return KnowledgeExplanation(knowledge=entry, trace=trace)
