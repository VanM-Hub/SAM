"""Environment-adaptive: belajar dari hasil TANPA authority baru.

Setelah remediasi + verifikasi, SAM mencatat kasus (entity label -> observasi
& apakah method efektif) sebagai MEMORI, BUKAN sebagai hak baru. Authority
tetap milik owner; memori ini hanya membuat observasi berikutnya lebih
efisien (mis. tahu sumber mana yang informatif), tidak pernah menaikkan
grant atau level otonomi.

Kunci (aturan Van): belajar TIDAK pernah memberi authority baru kepada SAM.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class Lesson:
    """Satu catatan hasil (dari observasi, bukan authority)."""

    entity_kind: str          # process/port/file (generik, bukan nama app)
    observation_source: str   # sumber yang informatif
    conclusion: str           # apa yang dipelajari (jujur)
    outcome: str              # ok / no_action / escalated / blocked
    count: int = 1

    def as_dict(self) -> Dict[str, Any]:
        return {
            "entity_kind": self.entity_kind,
            "observation_source": self.observation_source,
            "conclusion": self.conclusion,
            "outcome": self.outcome,
            "count": self.count,
        }


class AdaptiveMemory:
    """Memori ringan antar-run (in-memory, tidak menyentuh grant)."""

    def __init__(self) -> None:
        self._lessons: List[Lesson] = []
        self._updated_at: Dict[str, str] = {}

    def record(self, lesson: Lesson) -> None:
        # ringkas: gabung kalau observasi + conclusion sama
        for existing in self._lessons:
            if (existing.entity_kind == lesson.entity_kind
                    and existing.observation_source == lesson.observation_source
                    and existing.conclusion == lesson.conclusion):
                existing.count += 1
                self._updated_at[lesson.observation_source] = _now()
                return
        self._lessons.append(lesson)
        self._updated_at[lesson.observation_source] = _now()

    def source_reliability(self, source: str) -> float:
        """Seberapa sering sumber ini menghasilkan kesimpulan (0..1).

        Murni statistik observasi; TIDAK mengubah authority.
        """
        hits = [lesson for lesson in self._lessons
                if lesson.observation_source == source and lesson.outcome == "ok"]
        tot = [lesson for lesson in self._lessons
               if lesson.observation_source == source]
        if not tot:
            return 0.0
        return sum(lesson.count for lesson in hits) / sum(lesson.count for lesson in tot)

    def all_lessons(self) -> List[Lesson]:
        return list(self._lessons)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "lessons": [lesson.as_dict() for lesson in self._lessons],
            "source_reliability": {
                s: self.source_reliability(s)
                for s in {lesson.observation_source for lesson in self._lessons}
            },
            "updated_at": self._updated_at,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
