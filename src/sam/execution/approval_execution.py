# OP-395 — Execution Approval Bridge
# Python 3.8 compatible, frozen dataclass, synchronous only
# Converts ExecutionPlan → ApprovalRequest
# All execution MUST go through approval — no auto-submit

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .execution_request import (
    ExecutionRequest,
    ExecutionPlan,
    ExecutionStatus,
    ExecutionRisk,
)


# ---------------------------------------------------------------------------
# Approval DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ApprovalItem:
    """A single item requiring approval."""
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    action: str = ""
    connector_type: str = ""
    target_name: str = ""
    risk_level: str = ""
    risk_score: float = 0.0
    description: str = ""
    preview: str = ""


@dataclass(frozen=True)
class ApprovalRequest:
    """An approval request generated from an execution plan.

    All execution MUST go through this — no auto-submit.
    """
    approval_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str = ""
    items: Tuple[ApprovalItem, ...] = field(default_factory=tuple)
    total_items: int = 0
    requires_human: bool = True
    aggregated_risk_level: str = "low"
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    approved: bool = False
    approved_at: Optional[datetime] = None
    approved_by: str = ""
    rejection_reason: str = ""
    requires_rollback: bool = False


@dataclass(frozen=True)
class ApprovalResult:
    """Result after an approval decision."""
    approval_id: str = ""
    approved: bool = False
    approved_by: str = ""
    approved_at: Optional[datetime] = None
    rejection_reason: str = ""
    plan_id: str = ""


# ---------------------------------------------------------------------------
# ExecutionApprovalBridge
# ---------------------------------------------------------------------------

class ExecutionApprovalBridge:
    """Bridge between Execution Planner and Approval workflow.

    Converts ExecutionPlan → ApprovalRequest.
    Does NOT submit anything automatically.
    """

    @staticmethod
    def create_approval_request(plan: ExecutionPlan) -> ApprovalRequest:
        """Convert an execution plan into an approval request.

        Pure conversion — no submission, no side effects.
        Returns ApprovalRequest DTO.
        """
        items: List[ApprovalItem] = []

        for req in plan.requests:
            if req.requires_human_approval:
                items.append(ApprovalItem(
                    request_id=req.request_id,
                    action=req.action,
                    connector_type=req.connector_type,
                    target_name=req.target.name if req.target else "unknown",
                    risk_level=req.risk.level,
                    risk_score=req.risk.score,
                    description=req.description,
                    preview=req.as_preview(),
                ))

        agg_risk = plan.aggregated_risk
        requires_human = len(items) > 0
        risk_level = agg_risk.level if agg_risk else "low"

        return ApprovalRequest(
            plan_id=plan.plan_id,
            items=tuple(items),
            total_items=len(items),
            requires_human=requires_human,
            aggregated_risk_level=risk_level,
            description=f"Approval for {plan.total_requests} execution requests ({risk_level} risk)",
            requires_rollback=plan.rollback_required,
        )

    @staticmethod
    def approve(
        approval_request: ApprovalRequest,
        approved_by: str = "operator",
    ) -> ApprovalResult:
        """Record approval decision.

        Returns ApprovalResult — does NOT execute anything.
        """
        now = datetime.utcnow()
        return ApprovalResult(
            approval_id=approval_request.approval_id,
            approved=True,
            approved_by=approved_by,
            approved_at=now,
            plan_id=approval_request.plan_id,
        )

    @staticmethod
    def reject(
        approval_request: ApprovalRequest,
        approved_by: str = "operator",
        reason: str = "",
    ) -> ApprovalResult:
        """Record rejection decision."""
        return ApprovalResult(
            approval_id=approval_request.approval_id,
            approved=False,
            approved_by=approved_by,
            approved_at=datetime.utcnow(),
            rejection_reason=reason or "Rejected by operator",
            plan_id=approval_request.plan_id,
        )

    @staticmethod
    def is_approval_required(plan: ExecutionPlan) -> bool:
        """Check if a plan requires human approval."""
        return plan.requires_human_approval

    @staticmethod
    def get_approval_items(plan: ExecutionPlan) -> Tuple[ApprovalItem, ...]:
        """Get items that need approval from a plan."""
        req = ExecutionApprovalBridge.create_approval_request(plan)
        return req.items
