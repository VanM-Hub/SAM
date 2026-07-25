"""Approval Gate models for SAM Framework."""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid


class ApprovalStatus(str, Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    EXECUTED = "executed"


class ApprovalDecision(str, Enum):
    """Decision made on an approval request."""

    APPROVE = "approve"
    DENY = "deny"
    DEFER = "defer"


class ApprovalRequest(BaseModel):
    """A request for human approval on a recommendation."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recommendation_id: str
    severity: str
    title: str
    description: str
    action_hint: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    decision: Optional[ApprovalDecision] = None
    decided_by: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    decided_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": False,
        "str_strip_whitespace": True,
    }