"""Collaboration Workflow — Sprint 26 Fase 3.

Manages multi-step collaborative workflows where agents work together
on a sequence of tasks via delegation. Integrates with DelegationManager
and AgentProtocol for execution.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.collaboration.delegation import (
    DelegationManager,
    DelegationRequest,
    DelegationStatus,
)
from sam.persistence.database import Database


logger = structlog.get_logger()

WORKFLOW_STATUSES = frozenset({"PENDING", "RUNNING", "COMPLETED", "FAILED"})


class CollaborationWorkflow:
    """A sequence of collaborative tasks executed via delegation.

    Each step specifies the target agent (or capability), the payload,
    and optionally a timeout.
    """

    def __init__(
        self,
        id: str,
        name: str,
        steps: List[Dict[str, Any]],
        status: str = "PENDING",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        if status not in WORKFLOW_STATUSES:
            raise ValueError(
                f"Invalid workflow status '{status}'. "
                f"Must be one of {sorted(WORKFLOW_STATUSES)}"
            )
        self.id = id
        self.name = name
        self.steps = steps
        self.status = status
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "steps": json.dumps(self.steps),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CollaborationWorkflow:
        return cls(
            id=data["id"],
            name=data["name"],
            steps=_parse_steps(data.get("steps", "[]")),
            status=data.get("status", "PENDING"),
            created_at=_parse_dt(data.get("created_at")),
            updated_at=_parse_dt(data.get("updated_at")),
        )

    def __repr__(self) -> str:
        return (
            f"CollaborationWorkflow(id={self.id!r}, name={self.name!r}, "
            f"steps={len(self.steps)}, status={self.status!r})"
        )


def _parse_steps(val: Any) -> List[Dict[str, Any]]:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            return parsed if isinstance(parsed, list) else []
        except (ValueError, TypeError):
            return []
    return []


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class CollaborationWorkflowManager:
    """Manages the lifecycle and execution of collaboration workflows.

    Can execute workflows sequentially, creating delegation requests
    for each step and tracking progress.
    """

    def __init__(
        self,
        db: Database,
        delegation_manager: DelegationManager,
    ) -> None:
        self.db = db
        self.dm = delegation_manager
        self.logger = logger.bind(component="CollaborationWorkflowManager")

    async def create_workflow(self, workflow: CollaborationWorkflow) -> str:
        """Persist a new workflow definition.

        Args:
            workflow: The workflow to create.

        Returns:
            The workflow ID.
        """
        d = workflow.to_dict()
        await self.db.execute(
            """INSERT INTO collaboration_workflows
               (id, name, steps, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (d["id"], d["name"], d["steps"], d["status"],
             d["created_at"], d["updated_at"]),
        )
        self.logger.info(
            "Workflow created",
            workflow_id=workflow.id,
            name=workflow.name,
            num_steps=len(workflow.steps),
        )
        return workflow.id

    async def execute_workflow(self, workflow_id: str) -> str:
        """Execute all steps of a workflow sequentially.

        For each step, creates a DelegationRequest and records its
        ID as part of the step progress. The workflow status moves
        PENDING → RUNNING → COMPLETED / FAILED.

        Args:
            workflow_id: The workflow to execute.

        Returns:
            The workflow ID.

        Raises:
            ValueError: If workflow not found.
        """
        wf = await self.get_workflow(workflow_id)
        if wf is None:
            raise ValueError(f"Workflow not found: {workflow_id}")

        # Mark RUNNING
        await self._set_status(workflow_id, "RUNNING")

        delegation_ids: List[str] = []
        overall_failed = False

        for step_idx, step in enumerate(wf.steps):
            target = step.get("target_agent_id", "")
            capability = step.get("capability", "general")
            payload = step.get("payload", {})
            timeout = step.get("timeout_seconds", 60)

            delegation = DelegationRequest(
                id=str(uuid.uuid4()),
                task_id=str(uuid.uuid4()),
                sender_agent_id="system",
                target_agent_id=target,
                capability=capability,
                payload=payload,
                timeout_seconds=timeout,
            )
            await self.dm.request_delegation(delegation)
            delegation_ids.append(delegation.id)

            self.logger.info(
                "Workflow step submitted",
                workflow_id=workflow_id,
                step=step_idx,
                delegation_id=delegation.id,
                target=target,
            )

        # Store delegation IDs in the workflow steps
        wf.steps = self._merge_delegation_ids(wf.steps, delegation_ids)
        await self._update_steps(workflow_id, wf.steps)

        if overall_failed:
            await self._set_status(workflow_id, "FAILED")
            return workflow_id

        await self._set_status(workflow_id, "COMPLETED")
        self.logger.info(
            "Workflow completed",
            workflow_id=workflow_id,
            delegations=len(delegation_ids),
        )
        return workflow_id

    async def get_workflow(
        self, workflow_id: str
    ) -> Optional[CollaborationWorkflow]:
        """Get a workflow by ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM collaboration_workflows WHERE id = ?",
            (workflow_id,),
        )
        if row is None:
            return None
        return CollaborationWorkflow.from_dict(dict(row))

    async def get_workflow_status(self, workflow_id: str) -> str:
        """Get current workflow status."""
        wf = await self.get_workflow(workflow_id)
        if wf is None:
            raise ValueError(f"Workflow not found: {workflow_id}")
        return wf.status

    async def list_workflows(
        self, status: Optional[str] = None, limit: int = 50
    ) -> List[CollaborationWorkflow]:
        """List workflows, optionally filtered by status."""
        if status is not None and status not in WORKFLOW_STATUSES:
            raise ValueError(
                f"Invalid status filter '{status}'. "
                f"Must be one of {sorted(WORKFLOW_STATUSES)}"
            )
        if status:
            rows = await self.db.fetch_all(
                """SELECT * FROM collaboration_workflows
                   WHERE status = ? ORDER BY created_at DESC LIMIT ?""",
                (status, limit),
            )
        else:
            rows = await self.db.fetch_all(
                """SELECT * FROM collaboration_workflows
                   ORDER BY created_at DESC LIMIT ?""",
                (limit,),
            )
        return [CollaborationWorkflow.from_dict(dict(r)) for r in rows]

    # ── Internal ────────────────────────────────────────────────

    def _merge_delegation_ids(
        self, steps: List[Dict[str, Any]], delegation_ids: List[str]
    ) -> List[Dict[str, Any]]:
        merged = []
        for i, step in enumerate(steps):
            s = dict(step)
            if i < len(delegation_ids):
                s["delegation_id"] = delegation_ids[i]
            merged.append(s)
        return merged

    async def _set_status(self, workflow_id: str, status: str) -> None:
        now = datetime.now(timezone.utc)
        await self.db.execute(
            "UPDATE collaboration_workflows SET status = ?, updated_at = ? WHERE id = ?",
            (status, now.isoformat(), workflow_id),
        )

    async def _update_steps(
        self, workflow_id: str, steps: List[Dict[str, Any]]
    ) -> None:
        now = datetime.now(timezone.utc)
        await self.db.execute(
            "UPDATE collaboration_workflows SET steps = ?, updated_at = ? WHERE id = ?",
            (json.dumps(steps), now.isoformat(), workflow_id),
        )
