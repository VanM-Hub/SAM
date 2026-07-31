"""Skill History — riwayat skill (Sprint 168).

Phase XVI — Skill Runtime.
Mencatat riwayat registrasi. Read-only query.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class SkillHistoryEntry:
    """Satu entri riwayat skill (immutable)."""
    skill_id: str
    action: str
    version: str = "1.0.0"
    external_calls: int = 0


class SkillHistory:
    """Riwayat skill. Append + read-only query."""

    def __init__(self) -> None:
        self._entries: List[SkillHistoryEntry] = []

    def record(self, entry: SkillHistoryEntry) -> None:
        self._entries.append(entry)

    def entries(self, skill_id: str = None) -> List[SkillHistoryEntry]:
        if skill_id is None:
            return list(self._entries)
        return [e for e in self._entries if e.skill_id == skill_id]

    def count(self) -> int:
        return len(self._entries)
