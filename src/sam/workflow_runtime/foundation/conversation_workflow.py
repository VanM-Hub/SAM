"""Conversation Workflow Bridge — query read-only (Sprint 196)."""
from __future__ import annotations

from .workflow_registry import WorkflowRegistry


class ConversationWorkflowBridge:
    """Bridge conversation — status workflow read-only."""

    def __init__(self, registry: WorkflowRegistry) -> None:
        self._registry = registry

    def summary(self) -> dict:
        return {
            "total_Workflow": self._registry.count(),
            "preview_only": True,
        }

    def status(self, workflow_id: str) -> str:
        return "registered" if self._registry.exists(workflow_id) else "missing"
