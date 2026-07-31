"""Skill Index — indeks skill (Sprint 168).

Phase XVI — Skill Runtime.
Indeks memetakan kata kunci/tag ke skill. Read-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from ..foundation.skill_registry import SkillRegistry


@dataclass(frozen=True)
class SkillIndex:
    """Indeks skill (immutable)."""
    tag_index: Dict[str, List[str]] = field(default_factory=dict)


class SkillIndexer:
    """Pembuat indeks skill. Read-only, deterministik."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def build(self) -> SkillIndex:
        index: Dict[str, List[str]] = {}
        for sid in self._registry.list_ids():
            d = self._registry.find(sid)
            if d is None:
                continue
            for tag in d.tags:
                index.setdefault(tag, []).append(sid)
        return SkillIndex(tag_index=index)

    def find_by_tag(self, tag: str) -> List[str]:
        return list(self.build().tag_index.get(tag, []))
