"""Dashboard Catalog Bridge — 5 WorkflowCards (Sprint 200)."""
from __future__ import annotations

from ..dashboard import WorkflowCard
from ..model.workflow import Workflow
from .workflow_catalog import WorkflowCatalog
from .workflow_loader import WorkflowLoader


class DashboardCatalogBridge:
    """Bridge dashboard — 5 kartu untuk catalog workflow."""

    def __init__(self, catalog: WorkflowCatalog = None) -> None:
        self._catalog = catalog or WorkflowCatalog()
        self._loader = WorkflowLoader(self._catalog)

    def cards(self, workflow: Workflow = None):
        wf = workflow or Workflow("w0")
        return [
            WorkflowCard("ct.workflow", "catalog", "ready",
                         f"{wf.workflow_id} ({wf.step_count()} steps)",
                         "workflow", "ready"),
            WorkflowCard("ct.catalog", "catalog", "ready",
                         f"{self._catalog.count()} workflow(s) catalogued",
                         "catalog", "ready"),
            WorkflowCard("ct.index", "catalog", "ready",
                         "WorkflowIndex frozen (tuple step ids)", "index", "ready"),
            WorkflowCard("ct.no_read", "catalog", "ready",
                         "catalog: read-only, no file, no cache", "preview", "ready"),
            WorkflowCard("ct.version", "catalog", "ready",
                         "WorkflowVersionProvider 20.0.0", "version", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
