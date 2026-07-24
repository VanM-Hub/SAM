"""Institutional Memory — Sprint 25 Fase 1.

Stores and manages institutional knowledge, patterns, recommendations,
and lessons that persist across workflows and clusters.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.persistence.database import Database


logger = structlog.get_logger()


MEMORY_TYPES = frozenset({"KNOWLEDGE", "PATTERN", "RECOMMENDATION", "LESSON"})


class InstitutionalMemory:
    """A single entry in institutional memory.

    Each entry carries a confidence score, success/failure counters,
    and a source identifier (cluster_id, node_id, workflow_id).
    """

    def __init__(
        self,
        id: str,
        type: str,
        content: Dict[str, Any],
        source: str = "",
        confidence: float = 1.0,
        success_count: int = 0,
        failure_count: int = 0,
        last_used_at: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        if type not in MEMORY_TYPES:
            raise ValueError(f"Invalid memory type '{type}'. Must be one of {sorted(MEMORY_TYPES)}")
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {confidence}")
        self.id = id
        self.type = type
        self.content = content
        self.source = source
        self.confidence = confidence
        self.success_count = success_count
        self.failure_count = failure_count
        self.last_used_at = last_used_at
        now = datetime.now(timezone.utc)
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "content": json.dumps(self.content),
            "source": self.source,
            "confidence": self.confidence,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> InstitutionalMemory:
        return cls(
            id=data["id"],
            type=data["type"],
            content=json.loads(data["content"]) if isinstance(data["content"], str) else data["content"],
            source=data.get("source", ""),
            confidence=data.get("confidence", 1.0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            last_used_at=_parse_dt(data.get("last_used_at")),
            created_at=_parse_dt(data.get("created_at")),
            updated_at=_parse_dt(data.get("updated_at")),
        )

    def __repr__(self) -> str:
        return (
            f"InstitutionalMemory(id={self.id!r}, type={self.type!r}, "
            f"confidence={self.confidence:.2f}, "
            f"success={self.success_count}, failure={self.failure_count})"
        )


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


class InstitutionalMemoryManager:
    """Manages institutional memory entries with DB persistence."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.logger = logger.bind(component="InstitutionalMemoryManager")

    async def store(self, memory: InstitutionalMemory) -> None:
        """Store or overwrite an institutional memory entry."""
        d = memory.to_dict()
        await self.db.execute(
            """INSERT OR REPLACE INTO institutional_memory
               (id, type, content, source, confidence,
                success_count, failure_count, last_used_at,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                d["id"], d["type"], d["content"], d["source"], d["confidence"],
                d["success_count"], d["failure_count"], d["last_used_at"],
                d["created_at"], d["updated_at"],
            ),
        )
        self.logger.info("Memory stored", memory_id=memory.id, type=memory.type)

    async def get(self, memory_id: str) -> Optional[InstitutionalMemory]:
        """Retrieve a memory entry by ID."""
        row = await self.db.fetch_one(
            "SELECT * FROM institutional_memory WHERE id = ?", (memory_id,)
        )
        if row is None:
            return None
        return InstitutionalMemory.from_dict(dict(row))

    async def search(self, query: Dict[str, Any]) -> List[InstitutionalMemory]:
        """Search memory by type, source, and/or confidence floor.

        Supported keys:
          - type (str): exact match on memory type
          - source (str): substring match on source
          - min_confidence (float): minimum confidence filter
        """
        conditions: List[str] = []
        params: List[Any] = []

        if "type" in query:
            conditions.append("type = ?")
            params.append(query["type"])
        if "source" in query:
            conditions.append("source LIKE ?")
            params.append(f"%{query['source']}%")
        if "min_confidence" in query:
            conditions.append("confidence >= ?")
            params.append(query["min_confidence"])

        where = ""
        if conditions:
            where = " WHERE " + " AND ".join(conditions)

        sql = "SELECT * FROM institutional_memory" + where + " ORDER BY confidence DESC"
        rows = await self.db.fetch_all(sql, params)
        return [InstitutionalMemory.from_dict(dict(r)) for r in rows]

    async def update_success_rate(self, memory_id: str, success: bool) -> None:
        """Increment success_count or failure_count and bump updated_at."""
        col = "success_count" if success else "failure_count"
        now = datetime.now(timezone.utc).isoformat()
        await self.db.execute(
            f"UPDATE institutional_memory SET {col} = {col} + 1, "
            "last_used_at = ?, updated_at = ? WHERE id = ?",
            (now, now, memory_id),
        )
        self.logger.debug(
            "Memory rate updated",
            memory_id=memory_id,
            success=success,
        )

    async def get_most_successful(
        self, type: str, limit: int = 10
    ) -> List[InstitutionalMemory]:
        """Get most successful entries for a given type."""
        if type not in MEMORY_TYPES:
            raise ValueError(f"Invalid memory type '{type}'")
        rows = await self.db.fetch_all(
            "SELECT * FROM institutional_memory WHERE type = ? "
            "ORDER BY success_count DESC, confidence DESC LIMIT ?",
            (type, limit),
        )
        return [InstitutionalMemory.from_dict(dict(r)) for r in rows]
