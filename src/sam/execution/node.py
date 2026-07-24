"""
Execution Node models — the unit of execution within an Execution Graph.

Each ExecutionNode represents a single capability invocation with
input/output, dependency tracking, retry policy, and compensation
policy.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────


class NodeStatus(str, Enum):
    """Execution node lifecycle states."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    COMPENSATED = "COMPENSATED"
    SKIPPED = "SKIPPED"


class RetryBackoff(str, Enum):
    """Backoff strategy for retries."""

    LINEAR = "LINEAR"
    EXPONENTIAL = "EXPONENTIAL"


class CompensationOnFailure(str, Enum):
    """Action when a node fails."""

    ABORT = "ABORT"
    COMPENSATE = "COMPENSATE"
    RETRY = "RETRY"
    ESCALATE = "ESCALATE"


# ── Policy Models ─────────────────────────────────────────────────────


class RetryPolicy(BaseModel):
    """Controls automated retry behaviour on node failure."""

    max_attempts: int = Field(default=3, ge=1, description="Maximum retry attempts")
    backoff: RetryBackoff = Field(default=RetryBackoff.EXPONENTIAL, description="Backoff strategy")
    initial_delay: int = Field(default=1, ge=0, description="Initial delay in seconds")
    max_delay: int = Field(default=60, ge=1, description="Maximum delay in seconds")
    jitter: bool = Field(default=True, description="Add random jitter to delay")

    class Config:
        extra = "forbid"

    def delay_for_attempt(self, attempt: int) -> float:
        """Calculate delay for a given attempt number (1-based)."""
        import random

        attempt_index = max(attempt - 1, 0)

        if self.backoff == RetryBackoff.LINEAR:
            raw = self.initial_delay * (attempt_index + 1)
        else:  # EXPONENTIAL
            raw = self.initial_delay * (2 ** attempt_index)

        delay = min(raw, self.max_delay)

        if self.jitter:
            delay = delay * (0.5 + random.random())

        return max(0.0, delay)


class CompensationPolicy(BaseModel):
    """Defines compensation behaviour when a node fails."""

    compensation_node_id: Optional[str] = Field(
        default=None,
        description="Node ID to execute as compensation",
    )
    on_failure: CompensationOnFailure = Field(
        default=CompensationOnFailure.ABORT,
        description="Action to take on node failure",
    )

    class Config:
        extra = "forbid"


# ── Execution Node ───────────────────────────────────────────────────


class ExecutionNode(BaseModel):
    """A single node in an Execution Graph representing a capability invocation.

    Each node has:
    - Dependencies: list of node IDs that must complete before this node runs
    - Retry policy: how to retry on failure
    - Compensation policy: what to do when this node fails
    """

    id: str = Field(description="Unique node identifier (UUID)")
    graph_id: str = Field(description="Parent execution graph ID")
    capability_id: str = Field(description="Capability to invoke")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input parameters")
    outputs: Optional[Dict[str, Any]] = Field(
        default=None, description="Output results (populated after execution)"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="Node IDs that must complete before this node",
    )
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy, description="Retry configuration")
    compensation_policy: CompensationPolicy = Field(
        default_factory=CompensationPolicy,
        description="Compensation configuration",
    )
    status: NodeStatus = Field(default=NodeStatus.PENDING, description="Current lifecycle state")
    evidence_ids: List[str] = Field(
        default_factory=list,
        description="Evidence records linked to this execution",
    )
    started_at: Optional[datetime] = Field(default=None, description="When execution started")
    completed_at: Optional[datetime] = Field(default=None, description="When execution completed")

    class Config:
        extra = "forbid"

    @property
    def is_terminal(self) -> bool:
        """True if the node has reached a terminal state."""
        return self.status in (
            NodeStatus.COMPLETED,
            NodeStatus.FAILED,
            NodeStatus.COMPENSATED,
            NodeStatus.SKIPPED,
        )

    @property
    def is_ready(self) -> bool:
        """True if the node is PENDING (ready to execute)."""
        return self.status == NodeStatus.PENDING
