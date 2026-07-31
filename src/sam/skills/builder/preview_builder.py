"""Preview Builder — membangun preview skill (Sprint 166).

Phase XVI — Skill Runtime.
Menghasilkan preview aksi skill. Tidak execute. external_calls selalu 0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class SkillPreview:
    """Preview skill (immutable)."""
    preview_id: str
    skill_id: str = ""
    preview: bool = True
    executed: bool = False
    external_calls: int = 0
    steps: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


class PreviewBuilder:
    """Builder preview skill. external_calls selalu 0."""

    def build(
        self, preview_id: str, skill_id: str,
        steps: List[str] = None,
    ) -> SkillPreview:
        return SkillPreview(
            preview_id=preview_id, skill_id=skill_id,
            preview=True, executed=False, external_calls=0,
            steps=list(steps or []),
            notes=["dry-run: no execution performed"],
        )
