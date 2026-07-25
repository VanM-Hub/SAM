"""Execution context passed to capability executors."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import uuid

import structlog

from sam.evidence.store import EvidenceStore
from sam.knowledge.store import KnowledgeStore
from sam.models import CorrelationContext


class ExecutionContext:
    """Runtime information passed to capability executors.

    Attributes:
        execution_id: UUID of the overall execution.
        invocation_id: UUID of this specific capability call.
        workflow_id: Identifier of the workflow being executed (if any).
        step_name: Human-readable name of the step being executed.
        parent_context: Optional parent context (for sub-workflows).
        inputs: Input data for this step.
        outputs: Output data produced by this step.
        correlation: Correlation context for end-to-end tracking.
        logger: Structured logger bound with execution context.
    """

    def __init__(
        self,
        execution_id: uuid.UUID,
        workflow_id: str,
        step_name: str,
        parent_context: Optional["ExecutionContext"] = None,
        inputs: Optional[Dict[str, Any]] = None,
        evidence: Optional[EvidenceStore] = None,
        knowledge: Optional[KnowledgeStore] = None,
        services: Optional[Dict[str, Any]] = None,
        correlation: Optional[CorrelationContext] = None,
    ) -> None:
        self.execution_id: uuid.UUID = execution_id
        self.invocation_id: uuid.UUID = uuid.uuid4()
        self.workflow_id: str = workflow_id
        self.step_name: str = step_name
        self.parent_context: Optional[ExecutionContext] = parent_context
        self.inputs: Dict[str, Any] = dict(inputs or {})
        self.outputs: Dict[str, Any] = {}
        self.evidence: Optional[EvidenceStore] = evidence
        self.knowledge: Optional[KnowledgeStore] = knowledge
        # services is a dict of auxiliary services (e.g. configuration)
        self.services: Dict[str, Any] = dict(services or {})
        # correlation context for end-to-end tracking
        self.correlation: Optional[CorrelationContext] = correlation

        # Create a bound logger with contextual information
        base_logger = structlog.get_logger()
        log_kwargs = {
            "execution_id": str(self.execution_id),
            "invocation_id": str(self.invocation_id),
            "workflow_id": self.workflow_id,
            "step_name": self.step_name,
        }
        if self.correlation:
            log_kwargs["correlation_id"] = self.correlation.correlation_id
        self.logger = base_logger.bind(**log_kwargs)

    def set_output(self, key: str, value: any) -> None:  # noqa: ANN401
        """Store an output value that downstream steps can consume."""
        self.outputs[key] = value
        self.logger.debug("Output set", key=key, type=type(value).__name__)

    def get_output(self, key: str, default: any = None) -> any:  # noqa: ANN401
        """Retrieve an output previously stored by this or a parent context."""
        ctx: Optional[ExecutionContext] = self
        while ctx is not None:
            if key in ctx.outputs:
                return ctx.outputs[key]
            ctx = ctx.parent_context
        return default

    def update_inputs(self, extra: Dict[str, Any]) -> None:
        """Update the input dictionary (used by the workflow engine before invoking)."""
        self.inputs.update(extra)
        self.logger.debug("Inputs updated", keys=list(extra.keys()))