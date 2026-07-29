# OP-391 — Execution Request
# Python 3.8 compatible, frozen dataclass, synchronous only
# Core DTOs for Execution Connectors — no execute() method anywhere
# No domain/repository/storage/network imports

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid


# ---------------------------------------------------------------------------
# Enums / Status
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExecutionStatus:
    value: str = "pending"  # pending, planned, awaiting_approval, approved, rejected, executing, completed, failed, rolled_back

    @staticmethod
    def pending() -> "ExecutionStatus":
        return ExecutionStatus("pending")

    @staticmethod
    def planned() -> "ExecutionStatus":
        return ExecutionStatus("planned")

    @staticmethod
    def awaiting_approval() -> "ExecutionStatus":
        return ExecutionStatus("awaiting_approval")

    @staticmethod
    def approved() -> "ExecutionStatus":
        return ExecutionStatus("approved")

    @staticmethod
    def rejected() -> "ExecutionStatus":
        return ExecutionStatus("rejected")

    @staticmethod
    def executing() -> "ExecutionStatus":
        return ExecutionStatus("executing")

    @staticmethod
    def completed() -> "ExecutionStatus":
        return ExecutionStatus("completed")

    @staticmethod
    def failed() -> "ExecutionStatus":
        return ExecutionStatus("failed")

    @staticmethod
    def rolled_back() -> "ExecutionStatus":
        return ExecutionStatus("rolled_back")

    def is_terminal(self) -> bool:
        return self.value in ("completed", "failed", "rolled_back", "rejected")

    def can_approve(self) -> bool:
        return self.value == "awaiting_approval"

    def __str__(self) -> str:
        return self.value


# ---------------------------------------------------------------------------
# Execution Risk
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExecutionRisk:
    """Risk assessment for an execution request."""
    level: str = "low"  # low, medium, high, critical
    score: float = 0.0  # 0.0 - 1.0
    factors: Tuple[str, ...] = field(default_factory=tuple)
    requires_approval: bool = True
    requires_guardian: bool = False
    description: str = ""


# ---------------------------------------------------------------------------
# Execution Parameter
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExecutionParameter:
    """A single parameter for an execution target."""
    key: str = ""
    value: str = ""
    description: str = ""
    required: bool = False
    sensitive: bool = False


# ---------------------------------------------------------------------------
# Execution Target
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExecutionTarget:
    """The target system/resource for execution."""
    target_id: str = ""
    target_type: str = ""  # file, api, database, container, network, custom
    uri: str = ""
    name: str = ""
    description: str = ""
    parameters: Tuple[ExecutionParameter, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Execution Request (Core DTO — immutable, no execute)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExecutionRequest:
    """An execution request that MUST go through approval before execution.

    Immutable frozen dataclass. No execute() method.
    This is a PROPOSAL — never executed automatically.
    """
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    connector_type: str = ""
    action: str = ""
    target: Optional[ExecutionTarget] = None
    parameters: Tuple[ExecutionParameter, ...] = field(default_factory=tuple)
    status: ExecutionStatus = field(default_factory=lambda: ExecutionStatus.pending())
    risk: ExecutionRisk = field(default_factory=ExecutionRisk)
    source: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    requires_approval: bool = True
    requires_guardian: bool = False
    tags: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def requires_human_approval(self) -> bool:
        """Convenience: does this request need human approval?"""
        return self.requires_approval or self.risk.requires_approval

    def as_preview(self) -> str:
        """Human-readable preview string — no side effects."""
        target_str = self.target.name if self.target else "unknown"
        return f"[{self.connector_type}] {self.action} -> {target_str} [risk={self.risk.level}]"

    def with_status(self, new_status: ExecutionStatus) -> "ExecutionRequest":
        """Return a new request with updated status (immutable pattern)."""
        return ExecutionRequest(
            request_id=self.request_id,
            connector_type=self.connector_type,
            action=self.action,
            target=self.target,
            parameters=self.parameters,
            status=new_status,
            risk=self.risk,
            source=self.source,
            description=self.description,
            created_at=self.created_at,
            requires_approval=self.requires_approval,
            requires_guardian=self.requires_guardian,
            tags=self.tags,
        )


# ---------------------------------------------------------------------------
# Execution Plan
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExecutionPlan:
    """A plan for executing one or more execution requests.

    Includes dependency ordering, parallel groups, rollback requirements.
    """
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    requests: Tuple[ExecutionRequest, ...] = field(default_factory=tuple)
    dependency_order: Tuple[str, ...] = field(default_factory=tuple)  # request_id in order
    parallel_groups: Tuple[Tuple[str, ...], ...] = field(default_factory=tuple)  # groups of request_ids
    rollback_required: bool = False
    estimated_duration_seconds: int = 0
    aggregated_risk: Optional[ExecutionRisk] = None
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def total_requests(self) -> int:
        return len(self.requests)

    @property
    def requires_human_approval(self) -> bool:
        return any(r.requires_human_approval for r in self.requests)


# ---------------------------------------------------------------------------
# Execution Result (read-only — populated by external execution)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExecutionResult:
    """Result of an execution. Read-only — set externally after execution."""
    request_id: str = ""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: ExecutionStatus = field(default_factory=lambda: ExecutionStatus.pending())
    success: bool = False
    output: str = ""
    error_message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    result_data: Dict[str, Any] = field(default_factory=dict)
    tags: Tuple[str, ...] = field(default_factory=tuple)
