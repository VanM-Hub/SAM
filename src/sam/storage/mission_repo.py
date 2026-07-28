"""
MissionRepository — OP-133.

Repository untuk:
  - Mission state (MissionController)
  - Timeline events
  - Checkpoints
  - Workspace locks
  - Scheduler queue
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import json

from sam.storage import AbstractRepository, ConnectionManager


class MissionRepository(AbstractRepository):
    """Repository untuk mission state + timeline + checkpoints."""

    MISSION_COLUMNS = ['mission_id', 'name', 'state', 'metadata_json']

    def ensure_schema(self):
        """Schema dibuat oleh migration 001."""
        pass

    def to_row(self, obj: Any) -> dict:
        if hasattr(obj, 'to_dict'):
            d = obj.to_dict()
        elif isinstance(obj, dict):
            d = obj
        else:
            d = {}
        return {
            'mission_id': d.get('mission_id', ''),
            'name': d.get('name', ''),
            'state': d.get('state', 'CREATED'),
            'metadata_json': self.serialize_json(d.get('metadata', {})),
        }

    def save_mission(self, mission_id: str, name: str, state: str,
                     metadata: Optional[dict] = None):
        """Upsert mission state."""
        self.conn.execute("""
            INSERT INTO missions (mission_id, name, state, metadata_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(mission_id) DO UPDATE SET
                name = excluded.name,
                state = excluded.state,
                metadata_json = excluded.metadata_json,
                updated_at = CURRENT_TIMESTAMP
        """, (mission_id, name, state,
              self.serialize_json(metadata or {})))
        self.conn.commit()

    def get_mission(self, mission_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM missions WHERE mission_id = ?",
            (mission_id,)
        ).fetchone()
        if row is None:
            return None
        d = self.row_to_dict(row)
        d['metadata'] = self.deserialize_json(d.get('metadata_json', '{}'))
        return d

    def list_missions(self, state_filter: Optional[str] = None) -> List[dict]:
        if state_filter:
            rows = self.conn.execute(
                "SELECT * FROM missions WHERE state = ? ORDER BY created_at",
                (state_filter,)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM missions ORDER BY created_at"
            ).fetchall()
        result = []
        for r in rows:
            d = self.row_to_dict(r)
            d['metadata'] = self.deserialize_json(d.get('metadata_json', '{}'))
            result.append(d)
        return result

    def delete_mission(self, mission_id: str):
        self.conn.execute("DELETE FROM missions WHERE mission_id = ?",
                          (mission_id,))
        self.conn.commit()

    # --- Timeline ---

    def add_timeline_event(self, mission_id: str, event_type: str,
                           description: str = ""):
        self.conn.execute("""
            INSERT INTO mission_timeline (mission_id, event_type, description)
            VALUES (?, ?, ?)
        """, (mission_id, event_type, description))
        self.conn.commit()

    def get_timeline(self, mission_id: str,
                     event_type: Optional[str] = None) -> List[dict]:
        if event_type:
            rows = self.conn.execute("""
                SELECT * FROM mission_timeline
                WHERE mission_id = ? AND event_type = ?
                ORDER BY event_id
            """, (mission_id, event_type)).fetchall()
        else:
            rows = self.conn.execute("""
                SELECT * FROM mission_timeline
                WHERE mission_id = ?
                ORDER BY event_id
            """, (mission_id,)).fetchall()
        return [self.row_to_dict(r) for r in rows]

    def get_timeline_count(self, mission_id: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS cnt FROM mission_timeline WHERE mission_id = ?",
            (mission_id,)
        ).fetchone()
        return row['cnt'] if row else 0

    def list_all_timeline_mission_ids(self) -> List[str]:
        rows = self.conn.execute(
            "SELECT DISTINCT mission_id FROM mission_timeline"
        ).fetchall()
        return [r['mission_id'] for r in rows]

    # --- Checkpoints ---

    def save_checkpoint(self, mission_id: str, step_index: int,
                        state: str, note: str = ""):
        self.conn.execute("""
            INSERT INTO mission_checkpoints (mission_id, step_index, state, note)
            VALUES (?, ?, ?, ?)
        """, (mission_id, step_index, state, note))
        self.conn.commit()

    def get_checkpoint(self, mission_id: str) -> Optional[dict]:
        row = self.conn.execute("""
            SELECT * FROM mission_checkpoints
            WHERE mission_id = ?
            ORDER BY checkpoint_id DESC LIMIT 1
        """, (mission_id,)).fetchone()
        return self.row_to_dict(row) if row else None

    def get_checkpoints_all(self, mission_id: str) -> List[dict]:
        rows = self.conn.execute("""
            SELECT * FROM mission_checkpoints
            WHERE mission_id = ?
            ORDER BY checkpoint_id
        """, (mission_id,)).fetchall()
        return [self.row_to_dict(r) for r in rows]

    def clear_checkpoints(self, mission_id: str):
        self.conn.execute(
            "DELETE FROM mission_checkpoints WHERE mission_id = ?",
            (mission_id,))
        self.conn.commit()


class WorkspaceLockRepository(AbstractRepository):
    """Repository untuk workspace locks."""

    def ensure_schema(self):
        pass

    def to_row(self, obj: Any) -> dict:
        return {}

    def acquire_lock(self, resource: str, mission_id: str,
                     reason: str = "", timeout_minutes: int = 5) -> bool:
        """Coba acquire lock. Return True jika berhasil."""
        try:
            self.conn.execute("BEGIN IMMEDIATE")
            existing = self.conn.execute(
                "SELECT * FROM workspace_locks WHERE resource = ?", (resource,)
            ).fetchone()
            if existing:
                # Cek expired
                self.conn.rollback()
                return False
            self.conn.execute("""
                INSERT INTO workspace_locks (resource, mission_id, reason, timeout_minutes)
                VALUES (?, ?, ?, ?)
            """, (resource, mission_id, reason, timeout_minutes))
            self.conn.commit()
            return True
        except Exception:
            self.conn.rollback()
            return False

    def release_lock(self, resource: str, mission_id: str) -> bool:
        self.conn.execute(
            "DELETE FROM workspace_locks WHERE resource = ? AND mission_id = ?",
            (resource, mission_id)
        )
        self.conn.commit()
        return True

    def release_all(self, mission_id: str):
        self.conn.execute(
            "DELETE FROM workspace_locks WHERE mission_id = ?",
            (mission_id,))
        self.conn.commit()

    def get_lock(self, resource: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM workspace_locks WHERE resource = ?",
            (resource,)
        ).fetchone()
        return self.row_to_dict(row) if row else None

    def list_locks(self) -> List[dict]:
        rows = self.conn.execute("SELECT * FROM workspace_locks").fetchall()
        return [self.row_to_dict(r) for r in rows]

    def count_locks(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS cnt FROM workspace_locks").fetchone()
        return row['cnt'] if row else 0


class SchedulerQueueRepository(AbstractRepository):
    """Repository untuk scheduler queue."""

    def ensure_schema(self):
        pass

    def to_row(self, obj: Any) -> dict:
        return {}

    def enqueue(self, mission_id: str, priority: str = "NORMAL",
                resources: Optional[List[str]] = None):
        self.conn.execute("""
            INSERT INTO scheduler_queue (mission_id, priority, resources, status)
            VALUES (?, ?, ?, ?)
        """, (mission_id, priority,
              json.dumps(resources or []), 'pending'))
        self.conn.commit()

    def dequeue(self) -> Optional[dict]:
        """Ambil mission dengan prioritas tertinggi yang pending."""
        self.conn.execute("BEGIN IMMEDIATE")
        row = self.conn.execute("""
            SELECT * FROM scheduler_queue
            WHERE status = 'pending'
            ORDER BY
                CASE priority
                    WHEN 'CRITICAL' THEN 0
                    WHEN 'HIGH' THEN 1
                    WHEN 'NORMAL' THEN 2
                    WHEN 'LOW' THEN 3
                END,
                entry_id ASC
            LIMIT 1
        """).fetchone()
        if row is None:
            self.conn.rollback()
            return None
        d = self.row_to_dict(row)
        d['resources'] = json.loads(d.get('resources', '[]'))
        self.conn.execute(
            "UPDATE scheduler_queue SET status = 'running', updated_at = CURRENT_TIMESTAMP WHERE entry_id = ?",
            (d['entry_id'],))
        self.conn.commit()
        return d

    def mark_completed(self, mission_id: str):
        self.conn.execute(
            "UPDATE scheduler_queue SET status = 'completed', updated_at = CURRENT_TIMESTAMP WHERE mission_id = ?",
            (mission_id,))
        self.conn.commit()

    def mark_failed(self, mission_id: str):
        self.conn.execute(
            "UPDATE scheduler_queue SET status = 'failed', updated_at = CURRENT_TIMESTAMP WHERE mission_id = ?",
            (mission_id,))
        self.conn.commit()

    def mark_cancelled(self, mission_id: str):
        self.conn.execute(
            "UPDATE scheduler_queue SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE mission_id = ?",
            (mission_id,))
        self.conn.commit()

    def get_status(self, mission_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM scheduler_queue WHERE mission_id = ?",
            (mission_id,)
        ).fetchone()
        if row is None:
            return None
        d = self.row_to_dict(row)
        d['resources'] = json.loads(d.get('resources', '[]'))
        return d

    def list_by_status(self, status: str) -> List[dict]:
        rows = self.conn.execute(
            "SELECT * FROM scheduler_queue WHERE status = ? ORDER BY priority, entry_id",
            (status,)
        ).fetchall()
        result = []
        for r in rows:
            d = self.row_to_dict(r)
            d['resources'] = json.loads(d.get('resources', '[]'))
            result.append(d)
        return result

    def get_stats(self) -> dict:
        rows = self.conn.execute("""
            SELECT status, COUNT(*) AS cnt
            FROM scheduler_queue
            GROUP BY status
        """).fetchall()
        stats = {'total': 0}
        for r in rows:
            stats[r['status']] = r['cnt']
            stats['total'] += r['cnt']
        return stats

    def reset(self):
        self.conn.execute("DELETE FROM scheduler_queue")
        self.conn.commit()
