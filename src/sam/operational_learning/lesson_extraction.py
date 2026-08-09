"""Lesson Extraction - WP-14 (MISSION-4.3 / IP-4.3-002).

Mengekstrak pelajaran (lesson) dari kasus operasional. Deterministik,
berbasis evidence.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Tuple

from .case_repository import Case


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class Lesson:
    """Satu pelajaran yang diekstrak."""

    lesson_id: str
    source_case_id: str
    content: str
    category: str = "general"  # prevention | recovery | optimization | general
    source_evidence: Tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "lesson_id": self.lesson_id,
            "source_case_id": self.source_case_id,
            "content": self.content,
            "category": self.category,
            "source_evidence": list(self.source_evidence),
            "created_at": self.created_at,
        }


class LessonExtractor:
    """Menyusun pelajaran dari sebuah kasus."""

    @classmethod
    def extract(cls, case: Case) -> Lesson:
        if not case.outcome:
            category = "general"
            content = f"Observed case {case.title} without recorded outcome."
        elif "fail" in case.outcome.lower() or "error" in case.outcome.lower():
            category = "prevention"
            content = (
                f"Avoid repeating: {case.title}. Outcome: {case.outcome}."
            )
        elif "success" in case.outcome.lower() or "ok" in case.outcome.lower():
            category = "optimization"
            content = f"Reuse approach: {case.title}. Outcome: {case.outcome}."
        else:
            category = "general"
            content = f"Lesson from {case.title}: outcome {case.outcome}."
        return Lesson(
            lesson_id=uuid.uuid4().hex,
            source_case_id=case.case_id,
            content=content,
            category=category,
            source_evidence=case.evidence_ids,
        )
