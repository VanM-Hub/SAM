"""Self-Healing Reflection — Sprint 28 Fase 2.

Captures the outcome of a healing cycle — what was predicted,
what actually happened, and what lessons were learned — forming
a closed feedback loop for continuous improvement.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict
import structlog

from sam.persistence.database import Database


logger = structlog.get_logger()


class ReflectionRecord(BaseModel):
    """A single reflection entry from a self-healing cycle.

    Captures the full cycle: symptom → hypothesis → action →
    outcome → gap analysis → lessons.

    Attributes:
        id: Unique record identifier.
        cycle_id: Identifier linking to the healing cycle.
        symptom: The anomaly or symptom that triggered the cycle.
        hypothesis: What was believed to be the root cause.
        action_taken: What healing action was executed.
        expected_outcome: What was predicted to happen.
        actual_outcome: What actually happened.
        gap_analysis: Analysis of the gap between expected and actual.
        lessons: List of lessons learned (strings).
        confidence: Confidence in this reflection (0.0–1.0).
        success: Whether the healing cycle succeeded.
        timestamp: When the reflection was recorded.
        metadata: Additional structured context.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: f"refl_{uuid.uuid4().hex[:12]}")
    cycle_id: str
    symptom: str
    hypothesis: str = ""
    action_taken: str = ""
    expected_outcome: str = ""
    actual_outcome: str = ""
    gap_analysis: str = ""
    lessons: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    success: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "cycle_id": self.cycle_id,
            "symptom": self.symptom,
            "hypothesis": self.hypothesis,
            "action_taken": self.action_taken,
            "expected_outcome": self.expected_outcome,
            "actual_outcome": self.actual_outcome,
            "gap_analysis": self.gap_analysis,
            "lessons": self.lessons,
            "confidence": self.confidence,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> "ReflectionRecord":
        """Create from a database row dict."""
        return cls(
            id=row["id"],
            cycle_id=row["cycle_id"],
            symptom=row["symptom"],
            hypothesis=row.get("hypothesis", ""),
            action_taken=row.get("action_taken", ""),
            expected_outcome=row.get("expected_outcome", ""),
            actual_outcome=row.get("actual_outcome", ""),
            gap_analysis=row.get("gap_analysis", ""),
            lessons=_parse_json_list(row.get("lessons", "[]")),
            confidence=float(row.get("confidence", 0.0)),
            success=bool(row.get("success", False)),
            timestamp=_parse_dt(row.get("timestamp")) or datetime.now(timezone.utc),
            metadata=_parse_json_dict(row.get("metadata", "{}")),
        )


class ReflectionManager:
    """Manages reflection records — recording, querying, and analyzing
    healing cycle outcomes.

    Integrates with SelfHealingLoop to capture the 'Reflect' and
    'Learn' phases of the feedback loop.
    """

    def __init__(self, db: Optional[Database] = None) -> None:
        self._db = db
        self._logger = logger.bind(component="ReflectionManager")

    async def record_reflection(
        self,
        cycle_id: str,
        symptom: str,
        hypothesis: str = "",
        action_taken: str = "",
        expected_outcome: str = "",
        actual_outcome: str = "",
        gap_analysis: str = "",
        lessons: Optional[List[str]] = None,
        confidence: float = 0.0,
        success: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ReflectionRecord:
        """Record a new reflection entry.

        Returns:
            The created ReflectionRecord.
        """
        record = ReflectionRecord(
            cycle_id=cycle_id,
            symptom=symptom,
            hypothesis=hypothesis,
            action_taken=action_taken,
            expected_outcome=expected_outcome,
            actual_outcome=actual_outcome,
            gap_analysis=gap_analysis,
            lessons=lessons or [],
            confidence=confidence,
            success=success,
            metadata=metadata or {},
        )

        if self._db:
            await self._db.execute(
                """INSERT INTO reflection_records
                   (id, cycle_id, symptom, hypothesis, action_taken,
                    expected_outcome, actual_outcome, gap_analysis,
                    lessons, confidence, success, timestamp, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    record.id,
                    cycle_id,
                    symptom,
                    hypothesis,
                    action_taken,
                    expected_outcome,
                    actual_outcome,
                    gap_analysis,
                    json.dumps(lessons or []),
                    confidence,
                    1 if success else 0,
                    record.timestamp.isoformat(),
                    json.dumps(metadata or {}),
                ],
            )

        self._logger.info(
            "Reflection recorded",
            reflection_id=record.id,
            cycle_id=cycle_id,
            success=success,
            confidence=confidence,
        )
        return record

    async def get_reflections(
        self,
        cycle_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ReflectionRecord]:
        """Retrieve reflection records.

        Args:
            cycle_id: If provided, filter to a specific cycle.
            limit: Maximum records to return.
            offset: Pagination offset.

        Returns:
            List of ReflectionRecord objects.
        """
        if not self._db:
            return []

        if cycle_id:
            rows = await self._db.fetch_all(
                "SELECT * FROM reflection_records WHERE cycle_id = ? "
                "ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (cycle_id, limit, offset),
            )
        else:
            rows = await self._db.fetch_all(
                "SELECT * FROM reflection_records ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )

        return [ReflectionRecord.from_row(dict(r)) for r in rows]

    async def get_reflection(self, reflection_id: str) -> Optional[ReflectionRecord]:
        """Get a single reflection by ID."""
        if not self._db:
            return None

        row = await self._db.fetch_one(
            "SELECT * FROM reflection_records WHERE id = ?",
            (reflection_id,),
        )
        if row is None:
            return None
        return ReflectionRecord.from_row(dict(row))

    async def get_reflection_count(self, cycle_id: Optional[str] = None) -> int:
        """Get total reflection count, optionally filtered by cycle."""
        if not self._db:
            return 0

        if cycle_id:
            row = await self._db.fetch_one(
                "SELECT COUNT(*) as cnt FROM reflection_records WHERE cycle_id = ?",
                (cycle_id,),
            )
        else:
            row = await self._db.fetch_one(
                "SELECT COUNT(*) as cnt FROM reflection_records"
            )
        return row["cnt"] if row else 0

    async def get_lessons_summary(self) -> List[Dict[str, Any]]:
        """Aggregate lessons across all reflections.

        Returns:
            List of dicts: {lesson, count, avg_confidence, success_rate}
        """
        if not self._db:
            return []

        rows = await self._db.fetch_all(
            "SELECT lessons, confidence, success FROM reflection_records "
            "ORDER BY timestamp DESC LIMIT 200"
        )

        lesson_map: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            lessons = _parse_json_list(row.get("lessons", "[]"))
            conf = float(row.get("confidence", 0.0))
            succ = bool(row.get("success", False))
            for lesson in lessons:
                if lesson not in lesson_map:
                    lesson_map[lesson] = {"count": 0, "total_confidence": 0.0, "success_count": 0}
                lesson_map[lesson]["count"] += 1
                lesson_map[lesson]["total_confidence"] += conf
                if succ:
                    lesson_map[lesson]["success_count"] += 1

        result = []
        for lesson, data in sorted(
            lesson_map.items(), key=lambda x: x[1]["count"], reverse=True
        ):
            result.append({
                "lesson": lesson,
                "count": data["count"],
                "avg_confidence": round(
                    data["total_confidence"] / data["count"], 2
                ),
                "success_rate": round(
                    data["success_count"] / data["count"], 2
                ) if data["count"] > 0 else 0.0,
            })
        return result


# ── Helpers ─────────────────────────────────────────────────────────


def _parse_json_list(val: Any) -> list:
    if val is None:
        return []
    if isinstance(val, list):
        return val
    try:
        return json.loads(val)
    except (ValueError, TypeError):
        return []


def _parse_json_dict(val: Any) -> dict:
    if val is None:
        return {}
    if isinstance(val, dict):
        return val
    try:
        return json.loads(val)
    except (ValueError, TypeError):
        return {}


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None


__all__ = [
    "ReflectionRecord",
    "ReflectionManager",
]
