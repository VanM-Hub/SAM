"""Dashboard Workflow Bridge — 5 WorkflowCards (Sprint 196)."""
from __future__ import annotations

from ..dashboard import WorkflowCard
from .workflow_registry import WorkflowRegistry


class DashboardWorkflowBridge:
    """Bridge dashboard — 5 kartu untuk fondasi workflow."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def cards(self):
        n = self._registry.count()
        verdict = "ready" if n > 0 else "empty"
        return [
            WorkflowCard("fd.workflow", "foundation", verdict,
                         f"{n} workflow descriptor(s)", "workflow foundation", verdict),
            WorkflowCard("fd.descriptor", "foundation", "ready",
                         "WorkflowDescriptor frozen", "deterministic", "ready"),
            WorkflowCard("fd.capability", "foundation", "ready",
                         "WorkflowCapability frozen", "no-inference", "ready"),
            WorkflowCard("fd.contract", "foundation", "ready",
                         "WorkflowContract preview-only", "preview", "ready"),
            WorkflowCard("fd.metadata", "foundation", "ready",
                         "WorkflowMetadata version 20.0.0", "read-only", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
