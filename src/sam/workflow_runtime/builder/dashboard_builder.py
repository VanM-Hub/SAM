"""Dashboard Builder Bridge — 5 WorkflowCards (Sprint 198)."""
from __future__ import annotations

from ..dashboard import WorkflowCard
from ..model.workflow import Workflow
from .workflow_builder import WorkflowBuilder


class DashboardBuilderBridge:
    """Bridge dashboard — 5 kartu untuk builder workflow."""

    def cards(self, wf: Workflow = None):
        wf = wf or WorkflowBuilder().build("w0").workflow
        return [
            WorkflowCard("bd.workflow", "builder", "ready",
                         f"workflow {wf.workflow_id} ({wf.step_count()} steps)",
                         "workflow", "ready"),
            WorkflowCard("bd.step", "builder", "ready",
                         "StepBuilder composes DTO", "step", "ready"),
            WorkflowCard("bd.dep", "builder", "ready",
                         "DependencyBuilder - no resolution", "dependency", "ready"),
            WorkflowCard("bd.preview", "builder", "ready",
                         "WorkflowPreviewDTO scheduled=False ext=0", "preview", "ready"),
            WorkflowCard("bd.noinfer", "builder", "ready",
                         "builder: no scheduling, no reasoning, no runtime select",
                         "no-inference", "ready"),
        ]

    def overview_card(self):
        return self.cards()[0]
