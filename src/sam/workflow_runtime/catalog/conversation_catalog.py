"""Conversation Catalog Bridge — 5 query read-only (Sprint 200)."""
from __future__ import annotations

from ..model.workflow import Workflow
from .workflow_catalog import WorkflowCatalog
from .workflow_loader import WorkflowLoader
from .workflow_index import WorkflowIndexer
from .workflow_version import WorkflowVersionProvider
from .workflow_history import WorkflowHistory, WorkflowHistoryEntry


class ConversationCatalogBridge:
    """Bridge conversation — 5 query read-only catalog workflow."""

    def __init__(self, catalog: WorkflowCatalog = None) -> None:
        self._catalog = catalog or WorkflowCatalog()
        self._loader = WorkflowLoader(self._catalog)
        self._indexer = WorkflowIndexer()
        self._version = WorkflowVersionProvider()
        self._history = WorkflowHistory()

    def query_1_add(self, workflow: Workflow) -> dict:
        self._catalog.add(workflow)
        self._history.record(WorkflowHistoryEntry(
            workflow_id=workflow.workflow_id, action="created",
        ))
        return {"added": workflow.workflow_id, "count": self._catalog.count()}

    def query_2_load(self, workflow_id: str) -> dict:
        r = self._loader.load(workflow_id)
        return {"ok": r.ok, "detail": r.detail}

    def query_3_search(self, workflow_id: str, term: str) -> list:
        wf = self._catalog.get(workflow_id)
        if wf is None:
            return []
        return self._indexer.search(
            self._indexer.index(wf, []), term,
        )

    def query_4_version(self, workflow_id: str) -> dict:
        v = self._version.provide(workflow_id)
        return {"version": v.version, "workflow_id": v.workflow_id}

    def query_5_history(self, workflow_id: str) -> list:
        return [e.workflow_id for e in self._history.by_workflow(workflow_id)]
