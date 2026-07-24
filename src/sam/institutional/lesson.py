"""Lesson Model — Sprint 25 Fase 1.

Captures lessons learned from intent execution: what worked,
what failed, and actionable insights backed by evidence.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import structlog

from sam.persistence.database import Database


logger = structlog.get_logger()


class Lesson:
    """A lesson learned from an intent execution.

    Links to the intent and graph that produced the lesson,
    with evidence IDs for traceability.
    """

    def __init__(
        self,
        id: str,
        intent_id: str,
        graph_id: str,
        what_worked: str = "",
        what_failed: str = "",
        insight: str = "",
        confidence: float = 1.0,
        evidence_ids: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {confidence}")
        self.id = id
        self.intent_id = intent_id
        self.graph_id = graph_id
        self.what_worked = what_worked
        self.what_failed = what_failed
        self.insight = insight
        self.confidence = confidence
        self.evidence_ids = evidence_ids or []
        self.timestamp = timestamp or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "intent_id": self.intent_id,
            "graph_id": self.graph_id,
            "what_worked": self.what_worked,
            "what_failed": self.what_failed,
            "insight": self.insight,
            "confidence": self.confidence,
            "evidence_ids": json.dumps(self.evidence_ids),
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Lesson:
        return cls(
            id=data["id"],
            intent_id=data["intent_id"],
            graph_id=data["graph_id"],
            what_worked=data.get("what_worked", ""),
            what_failed=data.get("what_failed", ""),
            insight=data.get("insight", ""),
            confidence=data.get("confidence", 1.0),
            evidence_ids=_parse_json_list(data.get("evidence_ids", "[]")),
            timestamp=_parse_dt(data.get("timestamp")),
        )

    def __repr__(self) -> str:
        return (
            f"Lesson(id={self.id!r}, intent_id={self.intent_id!r}, "
            f"graph_id={self.graph_id!r}, confidence={self.confidence:.2f})"
        )


def _parse_json_list(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(v) for v in val]
    try:
        parsed = json.loads(val)
        return [str(v) for v in parsed] if isinstance(parsed, list) else []
    except (ValueError, TypeError):
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


class LessonManager:
    """Manages lesson records with DB persistence."""

    def __init__(self, db: Database) -> None:
        self.db = db
        self.logger = logger.bind(component="LessonManager")

    async def record_lesson(self, lesson: Lesson) -> None:
        """Record a new lesson."""
        d = lesson.to_dict()
        await self.db.execute(
            """INSERT INTO lessons
               (id, intent_id, graph_id, what_worked, what_failed,
                insight, confidence, evidence_ids, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                d["id"], d["intent_id"], d["graph_id"],
                d["what_worked"], d["what_failed"], d["insight"],
                d["confidence"], d["evidence_ids"], d["timestamp"],
            ),
        )
        self.logger.info(
            "Lesson recorded",
            lesson_id=lesson.id,
            intent_id=lesson.intent_id,
        )

    async def get_lessons(
        self,
        intent_id: Optional[str] = None,
        graph_id: Optional[str] = None,
    ) -> List[Lesson]:
        """Retrieve lessons, optionally filtered by intent_id or graph_id."""
        conditions: List[str] = []
        params: List[Any] = []

        if intent_id:
            conditions.append("intent_id = ?")
            params.append(intent_id)
        if graph_id:
            conditions.append("graph_id = ?")
            params.append(graph_id)

        where = ""
        if conditions:
            where = " WHERE " + " AND ".join(conditions)

        sql = "SELECT * FROM lessons" + where + " ORDER BY timestamp DESC"
        rows = await self.db.fetch_all(sql, params)
        return [Lesson.from_dict(dict(r)) for r in rows]
