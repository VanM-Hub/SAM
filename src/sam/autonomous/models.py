"""
Autonomous Models — Phase 1

Model data untuk Autonomous Operations: actions, approval, status, risk.
"""

import uuid
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class ActionType(str, Enum):
    RESTART = "restart"
    RECOVER = "recover"
    RESUME = "resume"
    ISOLATE = "isolate"
    ESCALATE = "escalate"


class AutonomousActionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AutonomousAction(BaseModel):
    """Tindakan autonomous yang akan / sedang / sudah dijalankan."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    action_type: ActionType
    target: str = ""  # component, workflow, plugin
    status: AutonomousActionStatus = AutonomousActionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    reason: str = ""
    confidence: float = 0.5
    risk_level: RiskLevel = RiskLevel.MEDIUM
    steps: List[str] = Field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    incident_id: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Permintaan approval untuk tindakan autonomous."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    action_id: str
    requester: str = "autonomous"  # autonomous, operator
    reason: str = ""
    status: str = "pending"  # pending, approved, denied
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow().replace(hour=23, minute=59, second=59))
