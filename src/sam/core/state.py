"""
Runtime State Store — persistent state snapshots for all runtime components.

Provides a unified store where daemon, service, workflow, job, and plugin
states are persisted to SQLite via the Database API, enabling full recovery
after restarts.

Optimistic locking via `version` field prevents stale writes.
"""
from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union

import structlog
from pydantic import BaseModel, Field, field_validator, model_validator

from .events import Event
from .event_bus import EventBus


# ── Enums ──────────────────────────────────────────────────────────────

class StateType(str, Enum):
    """Runtime component types that can persist state."""
    DAEMON = "DAEMON"
    SERVICE = "SERVICE"
    WORKFLOW = "WORKFLOW"
    JOB = "JOB"
    PLUGIN = "PLUGIN"


# ── Model ──────────────────────────────────────────────────────────────

class StateRecord(BaseModel):
    """A snapshot of a runtime component's state."""
    id: str
    type: StateType
    name: str
    status: str
    data: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime
    version: int = Field(default=1, ge=1)

    class Config:
        frozen = False  # mutable for updates
        use_enum_values = True  # store enum as str


# ── Events ─────────────────────────────────────────────────────────────

class StateSavedEvent(Event):
    """Published when a state record is saved."""
    type: str = "state.saved"
    state_id: str
    state_type: str
    state_name: str
    status: str


class StateDeletedEvent(Event):
    """Published when a state record is deleted."""
    type: str = "state.deleted"
    state_id: str
    state_type: str
    state_name: str


# ── Errors ─────────────────────────────────────────────────────────────

class StateStoreError(RuntimeError):
    """Base error for state store operations."""
    pass


class OptimisticLockError(StateStoreError):
    """Raised when a version conflict is detected."""
    def __init__(self, record_id: str, expected_version: int, actual_version: int):
        self.record_id = record_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            f"Version conflict for {record_id}: expected v{expected_version}, "
            f"actual v{actual_version}"
        )


class StateStore:
    """Persistent state store backed by SQLite via the Database API.

    Supports CRUD with optimistic locking. Optionally publishes events
    on save/delete when an EventBus is provided.
    """

    _TABLE = "runtime_state_store"

    def __init__(self, db, event_bus: Optional[EventBus] = None):
        """
        Args:
            db: Database instance with execute/fetch_one/fetch_all methods.
            event_bus: Optional EventBus for publishing state change events.
        """
        self._db = db
        self._event_bus = event_bus
        self._logger = structlog.get_logger()

    # ── Public API ───────────────────────────────────────────────────

    async def save(self, record: StateRecord) -> None:
        """Insert or update a state record (upsert with optimistic locking).

        If the record exists, version must match or OptimisticLockError is raised.
        Version is auto-incremented on successful update.
        """
        existing = await self._get_row(record.id)

        if existing:
            # Update path — optimistic lock check
            if record.version != existing["version"]:
                raise OptimisticLockError(
                    record_id=record.id,
                    expected_version=record.version,
                    actual_version=existing["version"],
                )
            new_version = record.version + 1
            sql = (
                f"UPDATE {self._TABLE} SET type=?, name=?, status=?, data=?, "
                "updated_at=?, version=? WHERE id=?"
            )
            params = [
                record.type.value if isinstance(record.type, StateType) else record.type,
                record.name,
                record.status,
                json.dumps(record.data, default=str),
                record.updated_at.isoformat(),
                new_version,
                record.id,
            ]
            await self._db_execute(sql, params)
            record.version = new_version
        else:
            # Insert path
            sql = (
                f"INSERT INTO {self._TABLE} "
                "(id, type, name, status, data, updated_at, version) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)"
            )
            params = [
                record.id,
                record.type.value if isinstance(record.type, StateType) else record.type,
                record.name,
                record.status,
                json.dumps(record.data, default=str),
                record.updated_at.isoformat(),
                record.version,
            ]
            await self._db_execute(sql, params)

        await self._publish(StateSavedEvent(
            id=record.id,
            source="state_store",
            state_id=record.id,
            state_type=str(record.type.value if isinstance(record.type, StateType) else record.type),
            state_name=record.name,
            status=record.status,
        ))
        self._logger.debug("state_saved", id=record.id, type=record.type, status=record.status)

    async def get(self, id: str) -> Optional[StateRecord]:
        """Get a state record by ID."""
        row = await self._get_row(id)
        return self._row_to_record(row) if row else None

    async def get_by_type(self, type: Union[StateType, str]) -> List[StateRecord]:
        """Get all records of a given type."""
        type_str = type.value if isinstance(type, StateType) else type
        rows = await self._db_fetch_all(
            f"SELECT * FROM {self._TABLE} WHERE type=? ORDER BY updated_at DESC",
            [type_str],
        )
        return [self._row_to_record(r) for r in rows if r]

    async def get_by_name(self, name: str) -> Optional[StateRecord]:
        """Get the first record matching a name (any type)."""
        row = await self._db_fetch_one(
            f"SELECT * FROM {self._TABLE} WHERE name=? ORDER BY updated_at DESC",
            [name],
        )
        return self._row_to_record(row) if row else None

    async def get_by_type_and_name(self, type_: Union[StateType, str], name: str) -> Optional[StateRecord]:
        """Get a record by type and name (uses UNIQUE constraint)."""
        type_str = type_.value if isinstance(type_, StateType) else type_
        row = await self._db_fetch_one(
            f"SELECT * FROM {self._TABLE} WHERE type=? AND name=?",
            [type_str, name],
        )
        return self._row_to_record(row) if row else None

    async def list(
        self, type: Optional[Union[StateType, str]] = None
    ) -> List[StateRecord]:
        """List all records, optionally filtered by type."""
        if type:
            type_str = type.value if isinstance(type, StateType) else type
            rows = await self._db_fetch_all(
                f"SELECT * FROM {self._TABLE} WHERE type=? ORDER BY updated_at DESC",
                [type_str],
            )
        else:
            rows = await self._db_fetch_all(
                f"SELECT * FROM {self._TABLE} ORDER BY type, updated_at DESC"
            )
        return [self._row_to_record(r) for r in rows if r]

    async def delete(self, id: str) -> bool:
        """Delete a state record. Returns True if a row was deleted."""
        row = await self._get_row(id)
        if not row:
            return False
        await self._db_execute(
            f"DELETE FROM {self._TABLE} WHERE id=?", [id]
        )
        await self._publish(StateDeletedEvent(
            id=id,
            source="state_store",
            state_id=id,
            state_type=row["type"],
            state_name=row["name"],
        ))
        self._logger.debug("state_deleted", id=id)
        return True

    async def clear(self) -> None:
        """Delete all state records (for testing)."""
        await self._db_execute(f"DELETE FROM {self._TABLE}")

    # ── Recovery ─────────────────────────────────────────────────────

    async def recover(self) -> Dict[str, List[StateRecord]]:
        """Load all state records grouped by type for recovery consumption.

        Returns:
            Dict mapping StateType → List[StateRecord] for all persisted states.
        """
        all_records = await self.list()
        grouped: Dict[str, List[StateRecord]] = {}
        for rec in all_records:
            key = str(rec.type.value if isinstance(rec.type, StateType) else rec.type)
            grouped.setdefault(key, []).append(rec)
        self._logger.info("state_recovered", total=len(all_records), types=list(grouped.keys()))
        return grouped

    # ── Private helpers ──────────────────────────────────────────────

    async def _get_row(self, id: str) -> Optional[dict]:
        return await self._db_fetch_one(
            f"SELECT * FROM {self._TABLE} WHERE id=?", [id]
        )

    def _row_to_record(self, row: dict) -> StateRecord:
        return StateRecord(
            id=row["id"],
            type=StateType(row["type"]),
            name=row["name"],
            status=row["status"],
            data=json.loads(row["data"]) if isinstance(row["data"], str) else (row["data"] or {}),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            version=row["version"],
        )

    async def _db_execute(self, sql: str, params=None):
        """Execute write query via Database API."""
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

    async def _publish(self, event) -> None:
        if self._event_bus:
            await self._event_bus.publish(event)
