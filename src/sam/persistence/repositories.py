"""Repository layer mapping domain objects to sqlite storage."""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from sam.persistence.database import Database
from sam.evidence.models import Evidence
from sam.knowledge.models import KnowledgeFact
from sam.patterns.models import PatternDetection
from sam.recommendations.models import Recommendation
import structlog


logger = structlog.get_logger()


class EvidenceRepository:
    def __init__(self, db: Database):
        self._db = db

    async def add(self, ev: Evidence, correlation_id: Optional[str] = None) -> None:
        await self._db.execute(
            "INSERT OR REPLACE INTO evidence (id, capability_id, execution_id, type, confidence, payload, timestamp, correlation_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [ev.id, ev.capability_id, ev.execution_id, ev.type.value, ev.confidence, json.dumps(ev.payload), ev.timestamp.isoformat(), correlation_id],
        )
        logger.debug("EvidenceRepository.add", id=ev.id, correlation_id=correlation_id)

    async def get(self, evidence_id: str) -> Optional[dict]:
        row = await self._db.fetch_one("SELECT * FROM evidence WHERE id = ?", [evidence_id])
        return row

    async def list(self, limit: int = 100) -> List[dict]:
        rows = await self._db.fetch_all("SELECT * FROM evidence ORDER BY timestamp DESC LIMIT ?", [limit])
        return rows


class KnowledgeRepository:
    def __init__(self, db: Database):
        self._db = db

    async def add(self, fact: KnowledgeFact, correlation_id: Optional[str] = None) -> None:
        await self._db.execute(
            "INSERT OR REPLACE INTO knowledge (id, capability_id, status, source, confidence, payload, timestamp, correlation_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [fact.id, fact.capability_id, fact.status.value, fact.source.value, fact.confidence, json.dumps(fact.model_dump(mode='json')), fact.timestamp.isoformat(), correlation_id],
        )
        logger.debug("KnowledgeRepository.add", id=fact.id, correlation_id=correlation_id)

    async def get(self, fact_id: str) -> Optional[dict]:
        return await self._db.fetch_one("SELECT * FROM knowledge WHERE id = ?", [fact_id])

    async def query(self, capability_id: Optional[str] = None, limit: int = 100) -> List[dict]:
        if capability_id:
            return await self._db.fetch_all("SELECT * FROM knowledge WHERE capability_id = ? ORDER BY timestamp DESC LIMIT ?", [capability_id, limit])
        return await self._db.fetch_all("SELECT * FROM knowledge ORDER BY timestamp DESC LIMIT ?", [limit])

    async def update_status(self, fact_id: str, status: Any) -> None:
        """Update the status of a knowledge fact."""
        await self._db.execute(
            "UPDATE knowledge SET status = ? WHERE id = ?",
            [status.value if hasattr(status, 'value') else status, fact_id]
        )
        logger.debug("KnowledgeRepository.update_status", id=fact_id, status=status.value if hasattr(status, 'value') else status)


class PatternRepository:
    def __init__(self, db: Database):
        self._db = db

    async def add(self, detection: PatternDetection, correlation_id: Optional[str] = None) -> None:
        await self._db.execute(
            "INSERT OR REPLACE INTO patterns (id, rule_id, severity, message, metadata, timestamp, correlation_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            [detection.id, detection.rule_id, detection.severity.value, detection.message, json.dumps(detection.metadata), detection.timestamp.isoformat(), correlation_id],
        )
        logger.debug("PatternRepository.add", id=detection.id, correlation_id=correlation_id)

    async def list(self, limit: int = 100) -> List[dict]:
        return await self._db.fetch_all("SELECT * FROM patterns ORDER BY timestamp DESC LIMIT ?", [limit])


class RecommendationRepository:
    def __init__(self, db: Database):
        self._db = db

    async def add(self, rec: Recommendation, correlation_id: Optional[str] = None) -> None:
        await self._db.execute(
            "INSERT OR REPLACE INTO recommendations (id, rule_id, pattern_detection_id, severity, title, description, action_hint, status, metadata, timestamp, correlation_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [rec.id, rec.rule_id, rec.pattern_detection_id, rec.severity.value, rec.title, rec.description, rec.action_hint, rec.status.value, json.dumps(rec.metadata), rec.timestamp.isoformat(), correlation_id],
        )
        logger.debug("RecommendationRepository.add", id=rec.id, correlation_id=correlation_id)

    async def list(self, limit: int = 100) -> List[dict]:
        return await self._db.fetch_all("SELECT * FROM recommendations ORDER BY timestamp DESC LIMIT ?", [limit])


class ApprovalRepository:
    def __init__(self, db: Database):
        self._db = db

    async def add(self, req, correlation_id: Optional[str] = None) -> None:
        """Persist an approval request.

        `req` diterima sebagai objek generik (dari layer pemanggil) — repository
        hanya membaca field, tidak bergantung pada tipe ApprovalRequest runtime
        (menghindari cross-layer import persistence → approval)."""
        await self._db.execute(
            "INSERT OR REPLACE INTO approvals (id, recommendation_id, severity, title, description, action_hint, status, decision, decided_by, decided_at, metadata, timestamp, correlation_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [req.id, req.recommendation_id, req.severity, req.title, req.description, req.action_hint, req.status.value, req.decision.value if req.decision else None, req.decided_by, req.decided_at.isoformat() if req.decided_at else None, json.dumps(req.metadata), req.timestamp.isoformat(), correlation_id],
        )
        logger.debug("ApprovalRepository.add", id=req.id, correlation_id=correlation_id)

    async def list(self, limit: int = 100) -> List[dict]:
        return await self._db.fetch_all("SELECT * FROM approvals ORDER BY timestamp DESC LIMIT ?", [limit])

    async def get_pending(self) -> List[dict]:
        return await self._db.fetch_all("SELECT * FROM approvals WHERE status = 'pending' ORDER BY timestamp DESC")


class WorkflowStateRepository:
    def __init__(self, db: Database):
        self._db = db

    async def create(self, state: dict) -> str:
        await self._db.execute(
            "INSERT INTO workflow_states (id, workflow_id, correlation_id, definition, current_step, status, started_at, completed_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [state["id"], state["workflow_id"], state["correlation_id"], state["definition"], state.get("current_step"), state["status"], state["started_at"], state.get("completed_at"), state.get("metadata", "{}")]
        )
        logger.debug("WorkflowStateRepository.create", workflow_id=state["workflow_id"])
        return state["id"]

    async def get(self, workflow_id: str) -> Optional[dict]:
        row = await self._db.fetch_one("SELECT * FROM workflow_states WHERE workflow_id = ?", [workflow_id])
        return row

    async def update(self, workflow_id: str, updates: dict) -> None:
        if not updates:
            return
        set_clauses = []
        params = []
        for key, value in updates.items():
            if key in ("workflow_id", "id"):
                continue
            set_clauses.append(f"{key} = ?")
            params.append(value)
        if not set_clauses:
            return
        params.append(workflow_id)
        await self._db.execute(
            f"UPDATE workflow_states SET {', '.join(set_clauses)} WHERE workflow_id = ?",
            params
        )
        logger.debug("WorkflowStateRepository.update", workflow_id=workflow_id, updates=list(updates.keys()))


class ScheduleRepository:
    """Repository for schedule persistence."""

    def __init__(self, db: Database):
        self._db = db

    async def create(self, schedule: dict) -> str:
        """Create a new schedule entry."""
        await self._db.execute(
            """INSERT INTO schedules (
                id, name, workflow_file, schedule_type, cron_expression,
                delay_seconds, max_retries, retry_delay, enabled,
                status, last_run, next_run, created_at, updated_at,
                run_count, last_error, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                schedule["id"],
                schedule["name"],
                schedule["workflow_file"],
                schedule["schedule_type"],
                schedule.get("cron_expression"),
                schedule.get("delay_seconds"),
                schedule["max_retries"],
                schedule["retry_delay"],
                schedule["enabled"],
                schedule["status"],
                schedule.get("last_run"),
                schedule.get("next_run"),
                schedule["created_at"],
                schedule["updated_at"],
                schedule.get("run_count", 0),
                schedule.get("last_error"),
                json.dumps(schedule.get("metadata", "{}")),
            ],
        )
        logger.debug("ScheduleRepository.create", id=schedule["id"], name=schedule["name"])
        return schedule["id"]

    async def get(self, schedule_id: str) -> Optional[dict]:
        """Get a schedule by ID."""
        row = await self._db.fetch_one("SELECT * FROM schedules WHERE id = ?", [schedule_id])
        if row and isinstance(row.get("metadata"), str):
            import json
            row["metadata"] = json.loads(row["metadata"])
        return row

    async def get_pending(self) -> List[dict]:
        """Get all schedules that are due to run."""
        now = datetime.utcnow().isoformat()
        rows = await self._db.fetch_all(
            """SELECT * FROM schedules
            WHERE enabled = 1
              AND status IN ('pending', 'running')
              AND (next_run IS NULL OR next_run <= ?)""",
            [now]
        )
        import json
        for row in rows:
            if isinstance(row.get("metadata"), str):
                row["metadata"] = json.loads(row["metadata"])
        return rows

    async def update(self, schedule_id: str, updates: dict) -> None:
        """Update a schedule."""
        if not updates:
            return
        set_clauses = []
        params = []
        for key, value in updates.items():
            if key in ("id",):
                continue
            set_clauses.append(f"{key} = ?")
            if key == "metadata" and isinstance(value, dict):
                import json
                params.append(json.dumps(value))
            elif isinstance(value, datetime):
                params.append(value.isoformat())
            else:
                params.append(value)
        if not set_clauses:
            return
        params.append(schedule_id)
        await self._db.execute(
            f"UPDATE schedules SET {', '.join(set_clauses)} WHERE id = ?",
            params
        )
        logger.debug("ScheduleRepository.update", schedule_id=schedule_id, updates=list(updates.keys()))

    async def list(self, limit: int = 100) -> List[dict]:
        """List schedules."""
        rows = await self._db.fetch_all(
            "SELECT * FROM schedules ORDER BY created_at DESC LIMIT ?",
            [limit]
        )
        import json
        for row in rows:
            if isinstance(row.get("metadata"), str):
                row["metadata"] = json.loads(row["metadata"])
        return rows