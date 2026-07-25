"""Human Escalation — Sprint 32.

Defines when and how to involve humans in autonomous operations.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()

STATUS_PENDING = "PENDING"
STATUS_RESOLVED = "RESOLVED"
STATUS_EXPIRED = "EXPIRED"

DECISION_APPROVE = "approve"
DECISION_REJECT = "reject"
DECISION_OVERRIDE = "override"
DECISION_MODIFY = "modify"

DEFAULT_ESCALATION_TTL = 3600  # 1 hour


@dataclass
class EscalationRequest:
    """A request escalated to a human operator.

    Attributes:
        id: Unique escalation ID.
        issue: Description of the issue.
        reason: Why human involvement is needed.
        context: Additional context (action, state, etc.).
        status: PENDING, RESOLVED, EXPIRED.
        decision: Human's decision (if resolved).
        created_at: When escalated.
        resolved_at: When resolved.
        ttl: Auto-expire after N seconds.
    """
    id: str = ""
    issue: str = ""
    reason: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    status: str = STATUS_PENDING
    decision: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    ttl: int = DEFAULT_ESCALATION_TTL

    def __post_init__(self) -> None:
        if not self.id:
            object.__setattr__(self, "id", f"esc_{uuid.uuid4().hex[:12]}")

    @property
    def expired(self) -> bool:
        if self.status != STATUS_PENDING:
            return False
        elapsed = (datetime.now(timezone.utc) - self.created_at).total_seconds()
        return elapsed > self.ttl

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "issue": self.issue,
            "reason": self.reason,
            "status": self.status,
            "decision": self.decision,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class EscalationManager:
    """Manages human escalation requests."""

    def __init__(self) -> None:
        self._escalations: Dict[str, EscalationRequest] = {}
        self.logger = logger.bind(component="EscalationManager")

    async def escalate(
        self,
        issue: str,
        reason: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> EscalationRequest:
        """Create a new escalation request."""
        req = EscalationRequest(
            issue=issue,
            reason=reason,
            context=context or {},
        )
        self._escalations[req.id] = req
        self.logger.info(
            "Escalation created",
            id=req.id,
            issue=issue,
            reason=reason,
        )
        return req

    async def get_pending_escalations(self) -> List[EscalationRequest]:
        """Get all PENDING escalations, auto-expiring stale ones."""
        result = []
        for req in self._escalations.values():
            if req.status == STATUS_PENDING and req.expired:
                req.status = STATUS_EXPIRED
            if req.status == STATUS_PENDING:
                result.append(req)
        return result

    async def resolve_escalation(
        self,
        escalation_id: str,
        decision: str,
    ) -> Optional[EscalationRequest]:
        """Resolve an escalation with a human decision."""
        req = self._escalations.get(escalation_id)
        if req is None:
            return None
        req.status = STATUS_RESOLVED
        req.decision = decision
        req.resolved_at = datetime.now(timezone.utc)
        self.logger.info(
            "Escalation resolved",
            id=escalation_id,
            decision=decision,
        )
        return req

    async def get_escalation(self, escalation_id: str) -> Optional[EscalationRequest]:
        return self._escalations.get(escalation_id)

    async def get_all_escalations(self, limit: int = 100) -> List[EscalationRequest]:
        result = list(self._escalations.values())
        result.sort(key=lambda r: r.created_at, reverse=True)
        return result[:limit]

    async def clear(self) -> None:
        self._escalations.clear()
