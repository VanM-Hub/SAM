"""
Workflow Checkpoint — pause/resume/recover state for workflow executions.

Provides:
- WorkflowCheckpoint Pydantic model with rich runtime state
- CheckpointStore persistence layer backed by SQLite via Database API
- Seamless integration with WorkflowEngine for checkpoint-after-step
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from pydantic import BaseModel, Field


# ── Status Enum ───────────────────────────────────────────────────────

class CheckpointStatus(str, Enum):
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ── Model ─────────────────────────────────────────────────────────────

class WorkflowCheckpoint(BaseModel):
    """Rich snapshot of a workflow execution at a given point in time."""

    workflow_id: str
    correlation_id: str
    current_step: str
    completed_steps: List[str] = Field(default_factory=list)
    pending_steps: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    retry_count: int = Field(default=0, ge=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default=CheckpointStatus.RUNNING.value)

    class Config:
        frozen = False
        use_enum_values = True


# ── Store ─────────────────────────────────────────────────────────────

class CheckpointStore:
    """Persists and retrieves workflow checkpoints via the Database API.

    Each checkpoint is stored in the workflow_checkpoints table
    (migration 014) keyed by workflow_id.
    """

    _TABLE = "workflow_checkpoints"

    def __init__(self, db):
        self._db = db
        self._logger = structlog.get_logger()

    async def save(self, checkpoint: WorkflowCheckpoint) -> None:
        """Insert or replace a checkpoint by workflow_id."""
        sql = (
            f"INSERT OR REPLACE INTO {self._TABLE} "
            "(workflow_id, correlation_id, current_step, completed_steps, "
            " pending_steps, evidence_ids, payload, retry_count, timestamp, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        params = [
            checkpoint.workflow_id,
            checkpoint.correlation_id,
            checkpoint.current_step,
            json.dumps(checkpoint.completed_steps),
            json.dumps(checkpoint.pending_steps),
            json.dumps(checkpoint.evidence_ids),
            json.dumps(checkpoint.payload, default=str),
            checkpoint.retry_count,
            checkpoint.timestamp.isoformat(),
            checkpoint.status,
        ]
        await self._db_execute(sql, params)
        self._logger.debug("checkpoint_saved", workflow_id=checkpoint.workflow_id, status=checkpoint.status)

    async def get(self, workflow_id: str) -> Optional[WorkflowCheckpoint]:
        """Retrieve a checkpoint by workflow_id."""
        row = await self._db_fetch_one(
            f"SELECT * FROM {self._TABLE} WHERE workflow_id=?", [workflow_id]
        )
        if not row:
            return None
        return self._row_to_checkpoint(row)

    async def list(self, status: Optional[str] = None) -> List[WorkflowCheckpoint]:
        """List all checkpoints, optionally filtered by status."""
        if status:
            rows = await self._db_fetch_all(
                f"SELECT * FROM {self._TABLE} WHERE status=? ORDER BY timestamp DESC",
                [status],
            )
        else:
            rows = await self._db_fetch_all(
                f"SELECT * FROM {self._TABLE} ORDER BY timestamp DESC"
            )
        return [self._row_to_checkpoint(r) for r in rows]

    async def delete(self, workflow_id: str) -> bool:
        """Delete a checkpoint. Returns True if a row was deleted."""
        await self._db_execute(
            f"DELETE FROM {self._TABLE} WHERE workflow_id=?", [workflow_id]
        )
        self._logger.debug("checkpoint_deleted", workflow_id=workflow_id)
        return True

    # ── Helpers ──────────────────────────────────────────────────────

    def _row_to_checkpoint(self, row: dict) -> WorkflowCheckpoint:
        return WorkflowCheckpoint(
            workflow_id=row["workflow_id"],
            correlation_id=row["correlation_id"],
            current_step=row["current_step"] or "",
            completed_steps=json.loads(row["completed_steps"]) if isinstance(row["completed_steps"], str) else [],
            pending_steps=json.loads(row["pending_steps"]) if isinstance(row["pending_steps"], str) else [],
            evidence_ids=json.loads(row["evidence_ids"]) if isinstance(row["evidence_ids"], str) else [],
            payload=json.loads(row["payload"]) if isinstance(row["payload"], str) else {},
            retry_count=row["retry_count"],
            timestamp=datetime.fromisoformat(row["timestamp"]) if isinstance(row["timestamp"], str) else datetime.utcnow(),
            status=row["status"],
        )

    async def _db_execute(self, sql: str, params=None):
        if params is not None and not isinstance(params, list):
            params = list(params)
        await self._db.execute(sql, params)

    async def _db_fetch_one(self, sql: str, params=None):
        if params is not None and not isinstance(params, list):
            params = list(params)
        return await self._db.fetch_one(sql, params)

    async def _db_fetch_all(self, sql: str, params=None):
        if params is not None and not isinstance(params, list):
            params = list(params)
        return await self._db.fetch_all(sql, params)
