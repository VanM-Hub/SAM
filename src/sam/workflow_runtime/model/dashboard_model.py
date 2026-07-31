"""Dashboard Model Bridge — 5 WorkflowCards (Sprint 197)."""
from __future__ import annotations

from ..dashboard import WorkflowCard
from .workflow import Workflow
from .workflow_validator import WorkflowValidator


class DashboardModelBridge:
    """Bridge dashboard — 5 kartu untuk model workflow."""

    def __init__(self) -> None:
        self._validator = WorkflowValidator()

    def cards(self, workflow: Workflow = None):
        wf = workflow or Workflow("wf0")
        return [
            WorkflowCard("md.workflow", "model", "ready",
                         f"{wf.workflow_id} ({wf.step_count()} steps)",
                         "workflow", "ready"),
            WorkflowCard("md.step", "model", "ready",
                         "WorkflowStep frozen", "step", "ready"),
            WorkflowCard("md.dep", "model", "ready",
                         "WorkflowDependency frozen", "dependency", "ready"),
            WorkflowCard("md.constraint", "model", "ready",
                         "WorkflowConstraint frozen", "constraint", "ready"),
            WorkflowCard("md.valid", "model", "ready",
                         "WorkflowValidator deterministic", "no-inference", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
