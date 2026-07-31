"""Workflow Version — versi workflow (Sprint 200)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowVersionInfo:
    """Info versi workflow (immutable)."""
    version: str = "20.0.0"
    workflow_id: str = ""
    runtime: str = "workflow_runtime"


class WorkflowVersionProvider:
    """Provider versi. Read-only, deterministik."""

    def provide(self, workflow_id: str) -> WorkflowVersionInfo:
        return WorkflowVersionInfo(version="20.0.0", workflow_id=workflow_id)
