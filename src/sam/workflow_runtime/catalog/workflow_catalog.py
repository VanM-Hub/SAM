"""Workflow Catalog — katalog workflow read-only (Sprint 200).

Tidak load file, tidak cache. Register hanya komposisi in-memory.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict

from ..model.workflow import Workflow


@dataclass(frozen=True)
class WorkflowCatalogEntry:
    """Entri katalog (immutable)."""
    workflow_id: str
    step_count: int = 0


class WorkflowCatalog:
    """Katalog workflow in-memory. Register hanya komposisi (no write/no file)."""

    def __init__(self) -> None:
        self._workflows: Dict[str, Workflow] = {}

    def add(self, workflow: Workflow) -> None:
        self._workflows[workflow.workflow_id] = workflow

    def get(self, workflow_id: str) -> Workflow | None:
        return self._workflows.get(workflow_id)

    def all_entries(self) -> List[WorkflowCatalogEntry]:
        return [
            WorkflowCatalogEntry(workflow_id=wf.workflow_id, step_count=wf.step_count())
            for wf in self._workflows.values()
        ]

    def count(self) -> int:
        return len(self._workflows)

    def by_scope(self, scope: str) -> List[Workflow]:
        return [wf for wf in self._workflows.values() if wf.scope == scope]
