"""Correlation models for end-to-end tracking across executions."""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CorrelationContext(BaseModel):
    """Context for correlating events across a workflow execution.

    Hierarchy: Correlation ID -> Workflow ID -> Execution ID -> Event ID

    Attributes:
        correlation_id: Root ID for the entire workflow/session (UUID).
        workflow_id: Identifier for the current workflow (optional).
        execution_id: Identifier for the current capability execution (optional).
        parent_id: Parent execution/workflow ID for nested workflows (optional).
        metadata: Additional contextual metadata.
    """

    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: Optional[str] = None
    execution_id: Optional[str] = None
    parent_id: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)

    @classmethod
    def new(
        cls,
        *,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> "CorrelationContext":
        """Create a new correlation context with a fresh correlation_id."""
        return cls(
            correlation_id=str(uuid4()),
            workflow_id=workflow_id,
            execution_id=execution_id,
            parent_id=parent_id,
            metadata=metadata or {},
        )

    @classmethod
    def child_of(
        cls,
        parent: "CorrelationContext",
        *,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> "CorrelationContext":
        """Create a child context inheriting the parent's correlation_id."""
        return cls(
            correlation_id=parent.correlation_id,
            workflow_id=workflow_id or parent.workflow_id,
            execution_id=execution_id or parent.execution_id,
            parent_id=parent.execution_id or parent.workflow_id,
            metadata={**parent.metadata, **(metadata or {})},
        )

    def with_workflow(self, workflow_id: str) -> "CorrelationContext":
        """Return a new context with the workflow_id set."""
        return self.model_copy(update={"workflow_id": workflow_id})

    def with_execution(self, execution_id: str) -> "CorrelationContext":
        """Return a new context with the execution_id set."""
        return self.model_copy(update={"execution_id": execution_id})

    def to_log_context(self) -> Dict:
        """Return a dict suitable for structlog binding."""
        return {
            "correlation_id": self.correlation_id,
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "parent_id": self.parent_id,
        }


def generate_correlation_id() -> str:
    """Generate a new correlation ID (UUID)."""
    return str(uuid4())


def generate_workflow_id() -> str:
    """Generate a new workflow ID."""
    return str(uuid4())


def generate_execution_id() -> str:
    """Generate a new execution ID."""
    return str(uuid4())