"""Workflow Builder — builder DTO workflow (Sprint 198).

Builder HANYA membangun DTO. Tidak scheduling, tidak reasoning,
tidak memilih runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..model.workflow import Workflow


@dataclass(frozen=True)
class WorkflowBuildResult:
    """Hasil build (immutable)."""
    ok: bool = True
    workflow: Workflow = field(default_factory=lambda: Workflow(""))
    detail: str = ""


class WorkflowBuilder:
    """Builder utama workflow. Deterministik."""

    def build(self, workflow_id: str, name: str = "", steps: list = None) -> WorkflowBuildResult:
        return WorkflowBuildResult(
            ok=True,
            workflow=Workflow(workflow_id=workflow_id, name=name, steps=list(steps or [])),
            detail="built",
        )
