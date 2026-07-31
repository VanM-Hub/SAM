"""Step Builder — membangun langkah skill (Sprint 166).

Phase XVI — Skill Runtime.
Builder hanya membangun langkah DTO. Tidak memilih runtime, tidak execute.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class SkillStep:
    """Langkah skill (immutable, build-only)."""
    step_id: str
    skill_id: str = ""
    order: int = 0
    action: str = "preview"
    inputs: Dict[str, Any] = field(default_factory=dict)
    preview_only: bool = True


class StepBuilder:
    """Builder langkah skill. Deterministik."""

    def build(
        self,
        step_id: str,
        skill_id: str,
        order: int = 0,
        action: str = "preview",
        inputs: Dict[str, Any] = None,
    ) -> SkillStep:
        return SkillStep(
            step_id=step_id, skill_id=skill_id, order=order,
            action=action, inputs=dict(inputs or {}),
        )
