"""Workflow Registry — registri workflow (Sprint 196)."""
from __future__ import annotations
from typing import Dict, List

from .workflow_descriptor import WorkflowDescriptor
from .workflow_capability import WorkflowCapability


class WorkflowRegistry:
    """Registri workflow. Register/attach hanya komposisi in-memory (no write)."""

    def __init__(self) -> None:
        self._descriptors: Dict[str, WorkflowDescriptor] = {}
        self._capabilities: Dict[str, List[WorkflowCapability]] = {}

    def register(self, descriptor: WorkflowDescriptor) -> None:
        self._descriptors[descriptor.id] = descriptor

    def attach_capability(self, capability: WorkflowCapability) -> None:
        self._capabilities.setdefault(capability.owner_id, []).append(capability)

    def get(self, workflow_id: str) -> WorkflowDescriptor | None:
        return self._descriptors.get(workflow_id)

    def exists(self, workflow_id: str) -> bool:
        return workflow_id in self._descriptors

    def all(self) -> List[WorkflowDescriptor]:
        return list(self._descriptors.values())

    def count(self) -> int:
        return len(self._descriptors)

    def capabilities(self, workflow_id: str) -> List[WorkflowCapability]:
        return list(self._capabilities.get(workflow_id, []))
