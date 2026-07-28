"""
OP-134, OP-135 — Decision & Approval Repositories.

DecisionRepository: proposals, history, execution plans, alternatives
ApprovalRepository: requests, reviewers, comments, status history
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sam.storage import AbstractRepository, ConnectionManager


class DecisionRepository(AbstractRepository):
    """Repository untuk decision proposals, history, execution plans."""

    DECISION_COLUMNS = ['decision_id', 'intent', 'context_json',
                        'reasoning_json', 'confidence', 'status']

    def ensure_schema(self):
        pass

    def to_row(self, obj: Any) -> dict:
        return {}

    def save_decision(self, decision_id: str, intent: str,
                      context: Optional[dict] = None,
                      reasoning: Optional[dict] = None,
                      confidence: float = 0.0,
                      status: str = "proposed"):
        self.conn.execute("""
            INSERT INTO decisions (decision_id, intent, context_json,
                                   reasoning_json, confidence, status)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(decision_id) DO UPDATE SET
                intent = excluded.intent,
                context_json = excluded.context_json,
                reasoning_json = excluded.reasoning_json,
                confidence = excluded.confidence,
                status = excluded.status,
                updated_at = CURRENT_TIMESTAMP
        """, (decision_id, intent,
              self.serialize_json(context or {}),
              self.serialize_json(reasoning or {}),
              confidence, status))
        self.conn.commit()

    def get_decision(self, decision_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM decisions WHERE decision_id = ?",
            (decision_id,)
        ).fetchone()
        if row is None:
            return None
        d = self.row_to_dict(row)
        d['context'] = self.deserialize_json(d.get('context_json', '{}'))
        d['reasoning'] = self.deserialize_json(d.get('reasoning_json', '{}'))
        return d

    def list_decisions(self, status_filter: Optional[str] = None,
                       limit: int = 100) -> List[dict]:
        if status_filter:
            rows = self.conn.execute("""
                SELECT * FROM decisions WHERE status = ?
                ORDER BY created_at DESC LIMIT ?
            """, (status_filter, limit)).fetchall()
        else:
            rows = self.conn.execute("""
                SELECT * FROM decisions ORDER BY created_at DESC LIMIT ?
            """, (limit,)).fetchall()
        return [self.row_to_dict(r) for r in rows]

    def list_decisions_today(self) -> List[dict]:
        rows = self.conn.execute("""
            SELECT * FROM decisions
            WHERE date(created_at) = date('now')
            ORDER BY created_at DESC
        """).fetchall()
        return [self.row_to_dict(r) for r in rows]

    # --- Decision History ---

    def record_change(self, decision_id: str, field_name: str,
                      old_value: str, new_value: str):
        self.conn.execute("""
            INSERT INTO decision_history (decision_id, field_name, old_value, new_value)
            VALUES (?, ?, ?, ?)
        """, (decision_id, field_name, old_value, new_value))
        self.conn.commit()

    def get_history(self, decision_id: str) -> List[dict]:
        rows = self.conn.execute("""
            SELECT * FROM decision_history
            WHERE decision_id = ?
            ORDER BY history_id
        """, (decision_id,)).fetchall()
        return [self.row_to_dict(r) for r in rows]

    def list_recent_changes(self, limit: int = 20) -> List[dict]:
        rows = self.conn.execute("""
            SELECT dh.*, d.intent
            FROM decision_history dh
            JOIN decisions d ON d.decision_id = dh.decision_id
            ORDER BY dh.changed_at DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [self.row_to_dict(r) for r in rows]

    # --- Execution Plans ---

    def save_plan(self, plan_id: str, decision_id: str,
                  steps: Optional[List[dict]] = None,
                  rationale: str = ""):
        self.conn.execute("""
            INSERT INTO execution_plans (plan_id, decision_id, steps_json, rationale)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(plan_id) DO UPDATE SET
                steps_json = excluded.steps_json,
                rationale = excluded.rationale
        """, (plan_id, decision_id,
              self.serialize_json(steps or []), rationale))
        self.conn.commit()

    def get_plan(self, plan_id: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM execution_plans WHERE plan_id = ?",
            (plan_id,)
        ).fetchone()
        if row is None:
            return None
        d = self.row_to_dict(row)
        d['steps'] = self.deserialize_json(d.get('steps_json', '[]'))
        return d

    def get_plans_for_decision(self, decision_id: str) -> List[dict]:
        rows = self.conn.execute(
            "SELECT * FROM execution_plans WHERE decision_id = ?",
            (decision_id,)
        ).fetchall()
        return [self.row_to_dict(r) for r in rows]

    # --- Alternatives ---

    def save_alternative(self, decision_id: str, label: str,
                         description: str = "",
                         impact: Optional[dict] = None,
                         score: float = 0.0):
        self.conn.execute("""
            INSERT INTO alternatives (decision_id, label, description, impact_json, score)
            VALUES (?, ?, ?, ?, ?)
        """, (decision_id, label, description,
              self.serialize_json(impact or {}), score))
        self.conn.commit()

    def get_alternatives(self, decision_id: str) -> List[dict]:
        rows = self.conn.execute("""
            SELECT * FROM alternatives WHERE decision_id = ?
            ORDER BY score DESC
        """, (decision_id,)).fetchall()
        result = []
        for r in rows:
            d = self.row_to_dict(r)
            d['impact'] = self.deserialize_json(d.get('impact_json', '{}'))
            result.append(d)
        return result

    def count_decisions(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS cnt FROM decisions").fetchone()
        return row['cnt'] if row else 0


class ApprovalRepository(AbstractRepository):
    """Repository untuk approval requests, history."""

    APPROVAL_COLUMNS = ['approval_id', 'decision_id', 'action_id',
                        'requestor', 'status', 'reviewer', 'reason', 'comment']

    def ensure_schema(self):
        pass

    def to_row(self, obj: Any) -> dict:
        return {}

    def save_approval(self, action_id: str,
                      decision_id: Optional[str] = None,
                      requestor: str = "SAM",
                      status: str = "pending",
                      reviewer: str = "",
                      reason: str = "",
                      comment: str = ""):
        self.conn.execute("""
            INSERT INTO approvals (decision_id, action_id, requestor, status,
                                   reviewer, reason, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (decision_id, action_id, requestor, status,
              reviewer, reason, comment))
        self.conn.commit()
        return self.conn.execute(
            "SELECT approval_id FROM approvals WHERE action_id = ? ORDER BY approval_id DESC LIMIT 1",
            (action_id,)
        ).fetchone()['approval_id']

    def get_approval(self, approval_id: int) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM approvals WHERE approval_id = ?",
            (approval_id,)
        ).fetchone()
        return self.row_to_dict(row) if row else None

    def update_status(self, approval_id: int, status: str,
                      reviewer: str = "", reason: str = "",
                      comment: str = ""):
        old = self.get_approval(approval_id)
        self.conn.execute("""
            UPDATE approvals SET status = ?, reviewer = ?, reason = ?,
                comment = ?, resolved_at = CURRENT_TIMESTAMP
            WHERE approval_id = ?
        """, (status, reviewer, reason, comment, approval_id))
        self.conn.commit()
        if old and old['status'] != status:
            self.record_change(approval_id, 'status', old['status'], status)

    def get_approvals_for_decision(self, decision_id: str) -> List[dict]:
        rows = self.conn.execute(
            "SELECT * FROM approvals WHERE decision_id = ? ORDER BY requested_at",
            (decision_id,)
        ).fetchall()
        return [self.row_to_dict(r) for r in rows]

    def list_pending(self) -> List[dict]:
        rows = self.conn.execute(
            "SELECT * FROM approvals WHERE status = 'pending' ORDER BY requested_at"
        ).fetchall()
        return [self.row_to_dict(r) for r in rows]

    def list_by_status(self, status: str) -> List[dict]:
        rows = self.conn.execute(
            "SELECT * FROM approvals WHERE status = ? ORDER BY requested_at DESC",
            (status,)
        ).fetchall()
        return [self.row_to_dict(r) for r in rows]

    def get_stats(self) -> dict:
        rows = self.conn.execute("""
            SELECT status, COUNT(*) AS cnt FROM approvals GROUP BY status
        """).fetchall()
        stats = {'total': 0}
        for r in rows:
            stats[r['status']] = r['cnt']
            stats['total'] += r['cnt']
        return stats

    def record_change(self, approval_id: int, field_name: str,
                      old_value: str, new_value: str):
        self.conn.execute("""
            INSERT INTO approvals_history (approval_id, field_name, old_value, new_value)
            VALUES (?, ?, ?, ?)
        """, (approval_id, field_name, old_value, new_value))
        self.conn.commit()


class AuditRepository(AbstractRepository):
    """Repository untuk audit events — append-only, immutable.

    Tidak ada DELETE, UPDATE, atau TRUNCATE.
    Hanya INSERT dan SELECT.
    """

    def ensure_schema(self):
        pass

    def to_row(self, obj: Any) -> dict:
        return {}

    def log_event(self, source: str, action: str,
                  actor: str = "SAM",
                  target_type: str = "",
                  target_id: str = "",
                  detail: Optional[dict] = None):
        """Append-only audit log. Tidak bisa dihapus."""
        self.conn.execute("""
            INSERT INTO audit_events (source, action, actor, target_type,
                                      target_id, detail_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (source, action, actor, target_type, target_id,
              self.serialize_json(detail or {})))
        self.conn.commit()

    def query(self, source: Optional[str] = None,
              action: Optional[str] = None,
              actor: Optional[str] = None,
              target_type: Optional[str] = None,
              target_id: Optional[str] = None,
              limit: int = 100) -> List[dict]:
        conditions = []
        params = []
        if source:
            conditions.append("source = ?"); params.append(source)
        if action:
            conditions.append("action = ?"); params.append(action)
        if actor:
            conditions.append("actor = ?"); params.append(actor)
        if target_type:
            conditions.append("target_type = ?"); params.append(target_type)
        if target_id:
            conditions.append("target_id = ?"); params.append(target_id)

        where = " AND ".join(conditions) if conditions else "1=1"
        rows = self.conn.execute("""
            SELECT * FROM audit_events WHERE {}
            ORDER BY event_id DESC LIMIT ?
        """.format(where), params + [limit]).fetchall()
        result = []
        for r in rows:
            d = self.row_to_dict(r)
            d['detail'] = self.deserialize_json(d.get('detail_json', '{}'))
            result.append(d)
        return result

    def count_events(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS cnt FROM audit_events").fetchone()
        return row['cnt'] if row else 0

    def list_sources(self) -> List[str]:
        rows = self.conn.execute(
            "SELECT DISTINCT source FROM audit_events ORDER BY source"
        ).fetchall()
        return [r['source'] for r in rows]

    def get_time_range(self) -> Optional[dict]:
        row = self.conn.execute("""
            SELECT MIN(created_at) AS first, MAX(created_at) AS last
            FROM audit_events
        """).fetchone()
        if row and row['first']:
            return {'first': row['first'], 'last': row['last']}
        return None
