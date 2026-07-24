"""Task Delegation — Sprint 26 Fase 3.

Manages the lifecycle of delegated tasks between agents:
REQUESTED → ACCEPTED → IN_PROGRESS → COMPLETED / FAILED
or REQUESTED → REJECTED, or → TIMEOUT.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog

from sam.persistence.database import Database


logger = structlog.get_logger()


class DelegationStatus(str, Enum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


_DELEGATION_TRANSITIONS = {
    DelegationStatus.REQUESTED: {DelegationStatus.ACCEPTED, DelegationStatus.REJECTED, DelegationStatus.TIMEOUT},
    DelegationStatus.ACCEPTED: {DelegationStatus.IN_PROGRESS, DelegationStatus.FAILED, DelegationStatus.TIMEOUT},
    DelegationStatus.IN_PROGRESS: {DelegationStatus.COMPLETED, DelegationStatus.FAILED, DelegationStatus.TIMEOUT},
    DelegationStatus.REJECTED: set(),
    DelegationStatus.COMPLETED: set(),
    DelegationStatus.FAILED: set(),
    DelegationStatus.TIMEOUT: set(),
}


class DelegationRequest:
    """A request to delegate a task from one agent to another."""

    def __init__(
        self,
        id: str,
        task_id: str,
        sender_agent_id: str,
        target_agent_id: str,
        capability: str,
        payload: Dict[str, Any],
        status: DeiStatus = DelegationStatus.REQUESTED,
        timeout_seconds: int = 60,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        self.id = id
        self.task_id = task_id
        self.sender_agent_id = sender_agent_id
        self.target_agent_id = target_agent_id
        self.capability = capability
        self.payload = payload
        self.status = _ensure_delegation_status(status)
        self.timeout_seconds = timeout_seconds
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now
        self.result = result
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "id": self.id,
            "task_id": self.task_id,
            "sender_agent_id": self.sender_agent_id,
            "target_agent_id": self.target_agent_id,
            "capability": self.capability,
            "payload": json.dumps(self.payload),
            "status": self.status.value,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if self.result is not None:
            d["result"] = json.dumps(self.result)
        if self.error is not None:
            d["error"] = self.error
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DelegationRequest:
        return cls(
            id=data["id"],
            task_id=data["task_id"],
            sender_agent_id=data["sender_agent_id"],
            target_agent_id=data["target_agent_id"],
            capability=data["capability"],
            payload=_parse_json_dict_(data.get("payload", "{}")),
            status=DelegationStatus(data.get("status", "REQUESTED")),
            timeout_seconds=data.get("timeout_seconds", 60),
            created_at=_parse_dt_(data.get("created_at")),
            updated_at=_parse_dt_(data.get("updated_at")),
            result=_parse_json_dict_(data.get("result")),
            error=data.get("error"),
        )

    def __repr__(self) -> str:
        return (
            f"DelegationRequest(id={self.id!r}, task={self.task_id!r}, "
            f"sender={self.sender_agent_id!r}, target={self.target_agent_id!r}, "
            f"status={self.status.value!r})"
        )


# Type alias to avoid long line-wraps
DeiStatus = DelegationStatus


def _ensure_delegation_status(v: Any) -> DelegationStatus:
    if isinstance(v, DelegationStatus):
        return v
    return DelegationStatus(v)


def _parse_json_dict_(val: Any) -> Dict[str, Any]:
    if val is None:
        return {}
    if isinstance(val, dict):
        return val
    try:
        parsed = json.loads(val)
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, TypeError):
        return {}


def _parse_dt_(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class DelegationManager:
    """Manages task delegation lifecycle between agents.

    Handles persistence, status transition validation,
    and provides query methods for pending/active delegations.
    """

    def __init__(self, db: Database) -> None:
        self.db = db
        self.logger = logger.bind(component="DelegationManager")

    async def request_delegation(self, request: DelegationRequest) -> str:
        """Submit a delegation request.

        Args:
            request: The delegation request to persist.

        Returns:
            The delegation ID.
        """
        d = request.to_dict()
        await self.db.execute(
            """INSERT INTO delegation_requests
               (id, task_id, sender_agent_id, target_agent_id,
                capability, payload, status, timeout_seconds,
                created_at, updated_at, result, error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                d["id"], d["task_id"], d["sender_agent_id"],
                d["target_agent_id"], d["capability"], d["payload"],
                d["status"], d["timeout_seconds"],
                d["created_at"], d["updated_at"],
                d.get("result"), d.get("error"),
            ),
        )
        self.logger.info(
            "Delegation requested",
            delegation_id=request.id,
            sender=request.sender_agent_id,
            target=request.target_agent_id,
            capability=request.capability,
        )
        return request.id

    async def accept_delegation(self, delegation_id: str) -> None:
        """Accept a delegation request (REQUESTED → ACCEPTED)."""
        dr = await self._get_or_raise(delegation_id)
        self._validate_transition(dr.status, DelegationStatus.ACCEPTED)
        await self._update_status(delegation_id, DelegationStatus.ACCEPTED)
        self.logger.info("Delegation accepted", delegation_id=delegation_id)

    async def reject_delegation(self, delegation_id: str, reason: str) -> None:
        """Reject a delegation request (REQUESTED → REJECTED)."""
        dr = await self._get_or_raise(delegation_id)
        self._validate_transition(dr.status, DelegationStatus.REJECTED)
        await self.db.execute(
            "UPDATE delegation_requests SET status = ?, updated_at = ?, error = ? WHERE id = ?",
            (DelegationStatus.REJECTED.value, datetime.now(timezone.utc).isoformat(), reason, delegation_id),
        )
        self.logger.info("Delegation rejected", delegation_id=delegation_id, reason=reason)

    async def start_delegation(self, delegation_id: str) -> None:
        """Mark delegation as in-progress (ACCEPTED → IN_PROGRESS)."""
        dr = await self._get_or_raise(delegation_id)
        self._validate_transition(dr.status, DelegationStatus.IN_PROGRESS)
        await self._update_status(delegation_id, DelegationStatus.IN_PROGRESS)
        self.logger.info("Delegation started", delegation_id=delegation_id)

    async def complete_delegation(
        self, delegation_id: str, result: Dict[str, Any]
    ) -> None:
        """Complete a delegation (IN_PROGRESS → COMPLETED)."""
        dr = await self._get_or_raise(delegation_id)
        self._validate_transition(dr.status, DelegationStatus.COMPLETED)
        now = datetime.now(timezone.utc)
        await self.db.execute(
            """UPDATE delegation_requests
               SET status = ?, updated_at = ?, result = ?
               WHERE id = ?""",
            (DelegationStatus.COMPLETED.value, now.isoformat(),
             json.dumps(result), delegation_id),
        )
        self.logger.info("Delegation completed", delegation_id=delegation_id)

    async def fail_delegation(
        self, delegation_id: str, error: str
    ) -> None:
        """Fail a delegation (IN_PROGRESS → FAILED)."""
        dr = await self._get_or_raise(delegation_id)
        self._validate_transition(dr.status, DelegationStatus.FAILED)
        now = datetime.now(timezone.utc)
        await self.db.execute(
            """UPDATE delegation_requests
               SET status = ?, updated_at = ?, error = ?
               WHERE id = ?""",
            (DelegationStatus.FAILED.value, now.isoformat(), error, delegation_id),
        )
        self.logger.info("Delegation failed", delegation_id=delegation_id, error=error)

    async def timeout_delegation(self, delegation_id: str) -> None:
        """Timeout a delegation (REQUESTED/ACCEPTED/IN_PROGRESS → TIMEOUT)."""
        dr = await self._get_or_raise(delegation_id)
        self._validate_transition(dr.status, DelegationStatus.TIMEOUT)
        now = datetime.now(timezone.utc)
        await self.db.execute(
            """UPDATE delegation_requests
               SET status = ?, updated_at = ?, error = ?
               WHERE id = ?""",
            (DelegationStatus.TIMEOUT.value, now.isoformat(),
             "Delegation timed out", delegation_id),
        )
        self.logger.info("Delegation timed out", delegation_id=delegation_id)

    async def get_delegation(
        self, delegation_id: str
    ) -> Optional[DelegationRequest]:
        """Get a delegation by ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM delegation_requests WHERE id = ?", (delegation_id,)
        )
        if row is None:
            return None
        return DelegationRequest.from_dict(dict(row))

    async def get_pending_for_agent(
        self, agent_id: str
    ) -> List[DelegationRequest]:
        """Get all REQUESTED delegations for a target agent."""
        rows = await self.db.fetch_all(
            """SELECT * FROM delegation_requests
               WHERE target_agent_id = ? AND status = 'REQUESTED'
               ORDER BY created_at ASC""",
            (agent_id,),
        )
        return [DelegationRequest.from_dict(dict(r)) for r in rows]

    async def get_active_for_agent(
        self, agent_id: str
    ) -> List[DelegationRequest]:
        """Get ACCEPTED or IN_PROGRESS delegations for an agent."""
        rows = await self.db.fetch_all(
            """SELECT * FROM delegation_requests
               WHERE target_agent_id = ? AND status IN ('ACCEPTED', 'IN_PROGRESS')
               ORDER BY created_at DESC""",
            (agent_id,),
        )
        return [DelegationRequest.from_dict(dict(r)) for r in rows]

    async def get_history_for_agent(
        self, agent_id: str, limit: int = 50
    ) -> List[DelegationRequest]:
        """Get all delegations involving an agent, newest first."""
        rows = await self.db.fetch_all(
            """SELECT * FROM delegation_requests
               WHERE sender_agent_id = ? OR target_agent_id = ?
               ORDER BY updated_at DESC LIMIT ?""",
            (agent_id, agent_id, limit),
        )
        return [DelegationRequest.from_dict(dict(r)) for r in rows]

    # ── Internal ────────────────────────────────────────────────

    async def _get_or_raise(self, delegation_id: str) -> DelegationRequest:
        dr = await self.get_delegation(delegation_id)
        if dr is None:
            raise ValueError(f"Delegation not found: {delegation_id}")
        return dr

    async def _update_status(
        self, delegation_id: str, new_status: DelegationStatus
    ) -> None:
        await self.db.execute(
            "UPDATE delegation_requests SET status = ?, updated_at = ? WHERE id = ?",
            (new_status.value, datetime.now(timezone.utc).isoformat(), delegation_id),
        )

    def _validate_transition(
        self, current: DelegationStatus, target: DelegationStatus
    ) -> None:
        allowed = _DELEGATION_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise ValueError(
                f"Cannot transition from {current.value} to {target.value}. "
                f"Allowed transitions from {current.value}: "
                f"{[s.value for s in allowed] or '<none>'}"
            )
