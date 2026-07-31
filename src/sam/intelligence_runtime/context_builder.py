"""Sprint 264 - Context Assembly: context_builder (menggabungkan section konteks)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .context_snapshot import ContextSnapshot


DEFAULT_SECTIONS = (
    "Mission", "Agent", "Workflow", "Skill", "Memory", "Knowledge",
    "Policy", "Audit", "Artifact", "Model", "Provider", "Execution",
)


@dataclass(frozen=True)
class ContextBuilder:
    """Builder deterministik: menyusun satu Context dari beberapa section."""

    _sections: Dict[str, Dict[str, object]]
    _order: tuple

    @classmethod
    def create(cls) -> "ContextBuilder":
        return cls(_sections={}, _order=DEFAULT_SECTIONS)

    def add(self, name: str, payload: Dict[str, object]) -> "ContextBuilder":
        sections = dict(self._sections)
        # hanya tambahkan section yang dikenal, supaya urutan deterministik
        if name in self._order:
            sections[name] = dict(payload)
        return ContextBuilder(_sections=sections, _order=self._order)

    def build(self) -> ContextSnapshot:
        ordered = {n: self._sections[n] for n in self._order if n in self._sections}
        return ContextSnapshot(sections=ordered, order=self._order)
