"""Workflow Builder — membangun workflow skill (Sprint 166).

Phase XVI — Skill Runtime.
Builder hanya menyusun urutan langkah DTO. Tidak memilih runtime, tidak execute.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .step_builder import SkillStep  # noqa: F401


@dataclass(frozen=True)
class SkillWorkflow:
    """Workflow skill (immutable, build-only)."""
    workflow_id: str
    skill_id: str = ""
    steps: List["SkillStep"] = field(default_factory=list)

    @property
    def step_count(self) -> int:
        return len(self.steps)


class WorkflowBuilder:
    """Builder workflow skill. Deterministik, build-only."""

    def build(self, workflow_id: str, skill_id: str = "") -> SkillWorkflow:
        return SkillWorkflow(workflow_id=workflow_id, skill_id=skill_id)
