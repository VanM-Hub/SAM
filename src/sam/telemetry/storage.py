import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .event import TelemetryEvent


class TelemetryStorage:
    """SQLite cache for telemetry events (offline support)."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = "./workspace/telemetry/cache.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    component TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    category TEXT NOT NULL,
                    message TEXT NOT NULL,
                    metadata TEXT,
                    correlation_id TEXT,
                    session_id TEXT,
                    workflow_id TEXT,
                    timestamp DATETIME NOT NULL,
                    duration_ms REAL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp
                ON telemetry_events(timestamp)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_telemetry_type
                ON telemetry_events(type)
            """)

    def save(self, event: TelemetryEvent) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO telemetry_events (
                    id, type, component, severity, category, message,
                    metadata, correlation_id, session_id, workflow_id,
                    timestamp, duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.id,
                event.type.value,
                event.component.value,
                event.severity.value,
                event.category.value,
                event.message,
                json.dumps(event.metadata),
                event.correlation_id,
                event.session_id,
                event.workflow_id,
                event.timestamp.isoformat(),
                event.duration_ms
            ))

    def query(self, limit: int = 100) -> List[TelemetryEvent]:
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("""
                SELECT * FROM telemetry_events
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [self._row_to_event(row) for row in rows]

    def count(self) -> int:
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM telemetry_events")
            return cursor.fetchone()[0]

    def _row_to_event(self, row) -> TelemetryEvent:
        from .event_type import TelemetryEventType
        from .component import Component
        from .event import EventSeverity, EventCategory

        return TelemetryEvent(
            id=row[0],
            type=TelemetryEventType(row[1]),
            component=Component(row[2]),
            severity=EventSeverity(row[3]),
            category=EventCategory(row[4]),
            message=row[5],
            metadata=json.loads(row[6]) if row[6] else {},
            correlation_id=row[7],
            session_id=row[8],
            workflow_id=row[9],
            timestamp=datetime.fromisoformat(row[10]),
            duration_ms=row[11]
        )

    def close(self) -> None:
        pass
