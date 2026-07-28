"""
OP-137 — Trust, Benchmark, Failure Pattern, Quality Repositories.

Histori persisten untuk semua metrik trust dan kualitas.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from sam.storage import AbstractRepository, ConnectionManager


class TrustRepository(AbstractRepository):
    """Repository untuk trust scores dan history."""

    def ensure_schema(self):
        pass

    def to_row(self, obj: Any) -> dict:
        return {}

    def save_score(self, decision_id: Optional[str], score: float,
                   grade: str = "C",
                   components: Optional[dict] = None) -> int:
        self.conn.execute("""
            INSERT INTO trust_scores (decision_id, score, grade, components_json)
            VALUES (?, ?, ?, ?)
        """, (decision_id, score, grade,
              self.serialize_json(components or {})))
        self.conn.commit()
        return self.conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

    def get_latest_score(self) -> Optional[dict]:
        row = self.conn.execute("""
            SELECT * FROM trust_scores ORDER BY calculated_at DESC LIMIT 1
        """).fetchone()
        if row is None:
            return None
        return self._row_to_score(row)

    def get_score_history(self, limit: int = 50) -> List[dict]:
        rows = self.conn.execute("""
            SELECT * FROM trust_scores ORDER BY calculated_at DESC LIMIT ?
        """, (limit,)).fetchall()
        return [self._row_to_score(r) for r in rows]

    def _row_to_score(self, row) -> dict:
        d = self.row_to_dict(row)
        d['components'] = self.deserialize_json(d.get('components_json', '{}'))
        return d

    def record_change(self, decision_id: Optional[str],
                      previous_score: float, new_score: float,
                      previous_grade: str, new_grade: str):
        # Find latest score_id
        latest = self.conn.execute(
            "SELECT score_id FROM trust_scores ORDER BY calculated_at DESC LIMIT 1"
        ).fetchone()
        score_id = latest['score_id'] if latest else None
        self.conn.execute("""
            INSERT INTO trust_history (score_id, decision_id, previous_score,
                                       new_score, previous_grade, new_grade)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (score_id, decision_id, previous_score, new_score,
              previous_grade, new_grade))
        self.conn.commit()

    def get_history(self, limit: int = 50) -> List[dict]:
        rows = self.conn.execute("""
            SELECT * FROM trust_history ORDER BY changed_at DESC LIMIT ?
        """, (limit,)).fetchall()
        return [self.row_to_dict(r) for r in rows]

    def is_trust_improved(self) -> Optional[bool]:
        """Apakah trust score terbaru lebih baik dari sebelumnya?"""
        scores = self.get_score_history(limit=2)
        if len(scores) < 2:
            return None
        return scores[0]['score'] > scores[1]['score']

    def count_scores(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS cnt FROM trust_scores").fetchone()
        return row['cnt'] if row else 0


class BenchmarkRepository(AbstractRepository):
    """Repository untuk benchmark results."""

    def ensure_schema(self):
        pass

    def to_row(self, obj: Any) -> dict:
        return {}

    def save_result(self, name: str, metrics: Optional[dict] = None,
                    overall_grade: str = "C"):
        self.conn.execute("""
            INSERT INTO benchmark_results (name, metrics_json, overall_grade)
            VALUES (?, ?, ?)
        """, (name, self.serialize_json(metrics or {}), overall_grade))
        self.conn.commit()

    def get_latest(self) -> Optional[dict]:
        row = self.conn.execute("""
            SELECT * FROM benchmark_results ORDER BY executed_at DESC LIMIT 1
        """).fetchone()
        if row is None:
            return None
        d = self.row_to_dict(row)
        d['metrics'] = self.deserialize_json(d.get('metrics_json', '{}'))
        return d

    def get_history(self, limit: int = 50) -> List[dict]:
        rows = self.conn.execute("""
            SELECT * FROM benchmark_results ORDER BY executed_at DESC LIMIT ?
        """, (limit,)).fetchall()
        result = []
        for r in rows:
            d = self.row_to_dict(r)
            d['metrics'] = self.deserialize_json(d.get('metrics_json', '{}'))
            result.append(d)
        return result

    def is_quality_decreased(self) -> Optional[bool]:
        """Apakah kualitas benchmark menurun?"""
        history = self.get_history(limit=2)
        if len(history) < 2:
            return None
        # Bandingkan overall_grade
        grades = {'A': 5, 'B': 4, 'C': 3, 'D': 2, 'E': 1}
        prev = grades.get(history[1].get('overall_grade', 'C'), 3)
        curr = grades.get(history[0].get('overall_grade', 'C'), 3)
        return curr < prev

    def count_benchmarks(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS cnt FROM benchmark_results").fetchone()
        return row['cnt'] if row else 0


class FailurePatternRepository(AbstractRepository):
    """Repository untuk failure patterns."""

    def ensure_schema(self):
        pass

    def to_row(self, obj: Any) -> dict:
        return {}

    def save_pattern(self, pattern_type: str, frequency: int = 1,
                     description: str = "", trend: str = "stable",
                     recommendation: str = ""):
        # Upsert by pattern_type
        existing = self.conn.execute(
            "SELECT pattern_id FROM failure_patterns WHERE pattern_type = ?",
            (pattern_type,)
        ).fetchone()
        if existing:
            self.conn.execute("""
                UPDATE failure_patterns SET frequency = ?, trend = ?,
                    last_observed = CURRENT_TIMESTAMP
                WHERE pattern_id = ?
            """, (frequency, trend, existing['pattern_id']))
        else:
            self.conn.execute("""
                INSERT INTO failure_patterns (pattern_type, frequency, description,
                                              trend, recommendation)
                VALUES (?, ?, ?, ?, ?)
            """, (pattern_type, frequency, description, trend, recommendation))
        self.conn.commit()

    def list_patterns(self) -> List[dict]:
        rows = self.conn.execute("""
            SELECT * FROM failure_patterns ORDER BY frequency DESC
        """).fetchall()
        return [self.row_to_dict(r) for r in rows]

    def get_by_type(self, pattern_type: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM failure_patterns WHERE pattern_type = ?",
            (pattern_type,)
        ).fetchone()
        return self.row_to_dict(row) if row else None

    def count_patterns(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS cnt FROM failure_patterns").fetchone()
        return row['cnt'] if row else 0


class DecisionQualityRepository(AbstractRepository):
    """Repository untuk decision quality assessments."""

    def ensure_schema(self):
        pass

    def to_row(self, obj: Any) -> dict:
        return {}

    def save_quality(self, decision_id: str,
                     metrics: Optional[dict] = None,
                     overall_score: float = 0.0):
        self.conn.execute("""
            INSERT INTO decision_quality (decision_id, metrics_json, overall_score)
            VALUES (?, ?, ?)
        """, (decision_id, self.serialize_json(metrics or {}), overall_score))
        self.conn.commit()

    def get_quality(self, decision_id: str) -> Optional[dict]:
        row = self.conn.execute("""
            SELECT * FROM decision_quality WHERE decision_id = ?
            ORDER BY assessed_at DESC LIMIT 1
        """, (decision_id,)).fetchone()
        if row is None:
            return None
        d = self.row_to_dict(row)
        d['metrics'] = self.deserialize_json(d.get('metrics_json', '{}'))
        return d

    def list_quality_history(self, limit: int = 50) -> List[dict]:
        rows = self.conn.execute("""
            SELECT dq.*, COALESCE(d.intent, '') AS intent
            FROM decision_quality dq
            LEFT JOIN decisions d ON d.decision_id = dq.decision_id
            ORDER BY dq.assessed_at DESC LIMIT ?
        """, (limit,)).fetchall()
        result = []
        for r in rows:
            d = self.row_to_dict(r)
            d['metrics'] = self.deserialize_json(d.get('metrics_json', '{}'))
            result.append(d)
        return result

    def count_quality(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS cnt FROM decision_quality").fetchone()
        return row['cnt'] if row else 0


class ReplayRepository(AbstractRepository):
    """Repository untuk decision replay results."""

    def ensure_schema(self):
        pass

    def to_row(self, obj: Any) -> dict:
        return {}

    def save_result(self, decision_id: str,
                    result: Optional[dict] = None):
        self.conn.execute("""
            INSERT INTO replay_results (decision_id, result_json)
            VALUES (?, ?)
        """, (decision_id, self.serialize_json(result or {})))
        self.conn.commit()

    def get_results_for_decision(self, decision_id: str) -> List[dict]:
        rows = self.conn.execute("""
            SELECT * FROM replay_results WHERE decision_id = ?
            ORDER BY replayed_at DESC
        """, (decision_id,)).fetchall()
        result = []
        for r in rows:
            d = self.row_to_dict(r)
            d['result'] = self.deserialize_json(d.get('result_json', '{}'))
            result.append(d)
        return result

    def count_replays(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS cnt FROM replay_results").fetchone()
        return row['cnt'] if row else 0
