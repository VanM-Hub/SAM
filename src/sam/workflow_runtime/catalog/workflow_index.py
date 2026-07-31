"""Workflow Index — indeks workflow (Sprint 200)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List

from ..model.workflow_step import WorkflowStep
from ..model.workflow import Workflow


@dataclass(frozen=True)
class WorkflowIndex:
    """Indeks workflow (immutable)."""
    workflow_id: str = ""
    step_count: int = 0
    step_ids: tuple = ()

    def has_step(self, step_id: str) -> bool:
        return step_id in self.step_ids


class WorkflowIndexer:
    """Indexer workflow. Read-only, deterministik."""

    def index(self, workflow: Workflow, steps: List[WorkflowStep]) -> WorkflowIndex:
        return WorkflowIndex(
            workflow_id=workflow.workflow_id,
            step_count=workflow.step_count(),
            step_ids=tuple(s.step_id for s in steps),
        )

    def search(self, index: WorkflowIndex, term: str) -> List[str]:
        return [sid for sid in index.step_ids if term in sid]
