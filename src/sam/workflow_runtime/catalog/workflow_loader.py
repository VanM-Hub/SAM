"""Workflow Loader — loader workflow read-only (Sprint 200).

Loader HANYA mengembalikan representasi yang sudah ada di memori —
tidak load file, tidak cache, TIDAK disk/IO.
"""
from __future__ import annotations
from dataclasses import dataclass

from ..model.workflow import Workflow
from .workflow_catalog import WorkflowCatalog


@dataclass(frozen=True)
class WorkflowLoadResult:
    """Hasil load (immutable)."""
    ok: bool = False
    workflow: Workflow | None = None
    detail: str = ""


class WorkflowLoader:
    """Loader workflow. Read-only (tanpa disk/IO, tanpa cache)."""

    def __init__(self, catalog: WorkflowCatalog) -> None:
        self._catalog = catalog

    def load(self, workflow_id: str) -> WorkflowLoadResult:
        wf = self._catalog.get(workflow_id)
        if wf is None:
            return WorkflowLoadResult(ok=False, detail="not found")
        return WorkflowLoadResult(ok=True, workflow=wf, detail="loaded")
