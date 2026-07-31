"""Workflow Summary — ringkasan workflow (Sprint 199)."""
from __future__ import annotations
from dataclasses import dataclass

from ..model.workflow import Workflow


@dataclass(frozen=True)
class WorkflowSummary:
    """Ringkasan (immutable)."""
    workflow_id: str = ""
    step_count: int = 0
    scope: str = ""


class WorkflowSummarizer:
    """Summarizer workflow. Deterministik."""

    def summarize(self, workflow: Workflow) -> WorkflowSummary:
        return WorkflowSummary(
            workflow_id=workflow.workflow_id,
            step_count=workflow.step_count(),
            scope=workflow.scope,
        )
