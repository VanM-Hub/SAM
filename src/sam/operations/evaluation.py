"""
Decision Evaluation — evaluasi setelah aksi selesai.

Setiap execution menghasilkan evaluation.
Membandingkan expected vs actual outcome.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

from .audit import AuditEventType, get_audit_trail


_EVALUATION_AUDIT_EVENT_SUCCESS = "execution_completed"
_EVALUATION_AUDIT_EVENT_FAILURE = "execution_failed"


@dataclass
class MetricChange:
    """Perubahan satu metrik setelah aksi."""
    metric: str          # cpu_percent, latency_ms, queue_depth, dll.
    before: float        # Sebelum action
    after: float         # Sesudah action
    expected: str        # "increase", "decrease", "unchanged"
    actual: str          # "increased", "decreased", "unchanged"
    recovered: bool = False  # Apakah kembali normal?

    def is_as_expected(self) -> bool:
        """Compare semantically: 'decrease' vs 'decreased', 'increase' vs 'increased'."""
        if self.expected == self.actual:
            return True
        if self.expected == "decrease" and self.actual == "decreased":
            return True
        if self.expected == "increase" and self.actual == "increased":
            return True
        return False

    def to_text(self) -> str:
        arrow = "✓" if self.is_as_expected() else "✗"
        return "{arrow} {metric}: {before:.0f} → {after:.0f} (expected {expected}, actual {actual})".format(
            arrow=arrow, metric=self.metric, before=self.before,
            after=self.after, expected=self.expected, actual=self.actual,
        )


@dataclass
class ActionOutcome:
    """Outcome untuk satu aksi."""
    action_title: str
    success: bool
    metric_changes: List[MetricChange] = field(default_factory=list)
    error_message: str = ""
    duration_ms: int = 0

    @property
    def metrics_met(self) -> int:
        return sum(1 for m in self.metric_changes if m.is_as_expected())

    @property
    def metrics_missed(self) -> int:
        return sum(1 for m in self.metric_changes if not m.is_as_expected())

    def to_text(self) -> str:
        parts = [
            "Action: {title} — {status}".format(
                title=self.action_title, status="PASSED" if self.success else "FAILED",
            ),
        ]
        if self.metric_changes:
            parts.append("Metrics: {met}/{total} as expected".format(
                met=self.metrics_met, total=len(self.metric_changes),
            ))
            for m in self.metric_changes:
                parts.append("  " + m.to_text())
        if self.error_message:
            parts.append("Error: {}".format(self.error_message))
        return "\n".join(parts)


@dataclass
class DecisionEvaluation:
    """Evaluasi satu keputusan yang sudah dieksekusi."""
    decision_title: str
    plan_id: str
    executed_at: str

    # Outcome keseluruhan
    overall_success: bool              # Apakah action sukses?
    outcome: str                       # "Success", "Failure", "Partial"

    # Quality metrics
    decision_accuracy: float = 0.0     # 0.0-1.0 — apakah keputusan tepat sasaran?
    recommendation_accuracy: float = 0.0  # 0.0-1.0 — seberapa akurat rekomendasi?
    prediction_accuracy: float = 0.0   # 0.0-1.0 — prediksi vs kenyataan

    # Metric-by-metric
    action_outcomes: List[ActionOutcome] = field(default_factory=list)

    # Overall
    recommendation_quality: str = ""   # "Excellent", "Good", "Poor", "Inconclusive"
    error_message: str = ""

    def to_text(self) -> str:
        lines = [
            "=== Decision Evaluation: {title} ===".format(title=self.decision_title),
            "Outcome: {outcome} | Overall: {success}".format(
                outcome=self.outcome, success="PASSED" if self.overall_success else "FAILED",
            ),
            "Decision accuracy: {:.0f}% | Recommendation accuracy: {:.0f}% | Prediction accuracy: {:.0f}%".format(
                self.decision_accuracy * 100,
                self.recommendation_accuracy * 100,
                self.prediction_accuracy * 100,
            ),
            "Quality: {q}".format(q=self.recommendation_quality),
        ]
        if self.action_outcomes:
            lines.append("")
            lines.append("Action outcomes ({count}):".format(count=len(self.action_outcomes)))
            for a in self.action_outcomes:
                lines.append(a.to_text())
        if self.error_message:
            lines.append("")
            lines.append("Error: {e}".format(e=self.error_message))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "decision_title": self.decision_title,
            "plan_id": self.plan_id,
            "overall_success": self.overall_success,
            "outcome": self.outcome,
            "decision_accuracy": self.decision_accuracy,
            "recommendation_accuracy": self.recommendation_accuracy,
            "prediction_accuracy": self.prediction_accuracy,
            "recommendation_quality": self.recommendation_quality,
            "action_count": len(self.action_outcomes),
        }


class EvaluationEngine:
    """Engine untuk mengevaluasi keputusan setelah eksekusi.

    Method utama:
      evaluate(decision_title, plan_id, expected, actual) -> DecisionEvaluation
    """

    def __init__(self):
        self._audit = get_audit_trail()
        self._history: Dict[str, List[bool]] = {}  # decision_title → [success, ...]

    def evaluate(self, decision_title: str,
                 plan_id: str,
                 expected_changes: Dict[str, str],
                 actual_metrics: Dict[str, Dict[str, float]],
                 action_success: bool = True,
                 action_details: Optional[List[Dict[str, Any]]] = None) -> DecisionEvaluation:
        """Evaluasi satu keputusan.

        Args:
            decision_title: Judul keputusan
            plan_id: ID plan yang dieksekusi
            expected_changes: Expected metric direction {'cpu': 'decrease', ...}
            actual_metrics: Actual values {'cpu': {'before': 90, 'after': 45}, ...}
            action_success: Apakah action sukses dieksekusi?
            action_details: Detail per action

        Returns:
            DecisionEvaluation
        """
        action_details = action_details or []

        # 1. Hitung metric changes + accuracy
        action_outcomes = []
        metric_accuracy_count = 0
        total_metrics = len(expected_changes)

        for metric, expected_direction in expected_changes.items():
            actual = actual_metrics.get(metric, {})
            before = actual.get("before", 0.0)
            after = actual.get("after", 0.0)

            # Determine actual direction
            if abs(after - before) < 0.5:
                actual_direction = "unchanged"
            elif after > before:
                actual_direction = "increased"
            else:
                actual_direction = "decreased"

            as_expected = (
                (expected_direction == "decrease" and actual_direction == "decreased") or
                (expected_direction == "increase" and actual_direction == "increased") or
                (expected_direction == "unchanged" and actual_direction == "unchanged")
            )

            if as_expected:
                metric_accuracy_count += 1

            mc = MetricChange(
                metric=metric,
                before=before,
                after=after,
                expected=expected_direction,
                actual=actual_direction,
                recovered=as_expected,
            )
            action_outcomes.append(ActionOutcome(
                action_title=metric,
                success=as_expected,
                metric_changes=[mc],
                duration_ms=actual.get("duration_ms", 0),
            ))

        # 2. Hitung overall accuracy
        decision_accuracy = metric_accuracy_count / max(1, total_metrics)

        # 3. Recommendation accuracy = dari historis
        self._history.setdefault(decision_title, []).append(action_success)
        history = self._history[decision_title]
        recent = history[-5:]  # last 5
        recommendation_accuracy = sum(1 for s in recent if s) / max(1, len(recent))

        # 4. Prediction accuracy = simplified
        prediction_accuracy = decision_accuracy * 0.9  # simplified estimate

        # 5. Outcome
        if action_success and decision_accuracy >= 0.7:
            outcome = "Success"
            quality = "Excellent"
        elif action_success and decision_accuracy >= 0.4:
            outcome = "Partial"
            quality = "Good"
        elif not action_success:
            outcome = "Failure"
            quality = "Poor"
            if decision_accuracy < 0.3:
                quality = "Poor"
        else:
            outcome = "Partial"
            quality = "Good"

        evaluation = DecisionEvaluation(
            decision_title=decision_title,
            plan_id=plan_id,
            executed_at=datetime.now().isoformat(),
            overall_success=action_success,
            outcome=outcome,
            decision_accuracy=round(decision_accuracy, 2),
            recommendation_accuracy=round(recommendation_accuracy, 2),
            prediction_accuracy=round(prediction_accuracy, 2),
            action_outcomes=[a for a in action_outcomes if any(m.recovered for m in a.metric_changes) is not None],
            recommendation_quality=quality,
        )

        # Audit entry
        audit_event_name = _EVALUATION_AUDIT_EVENT_SUCCESS if action_success else _EVALUATION_AUDIT_EVENT_FAILURE
        audit_event = AuditEventType(audit_event_name)
        self._audit.record(
            audit_event,
            plan_id, "evaluation_engine",
            "Evaluation: {decision} → {outcome} (acc={accuracy:.0f}%)".format(
                decision=decision_title[:40],
                outcome=outcome,
                accuracy=decision_accuracy * 100,
            ),
            description="Metrics: {met}/{total} as expected. Quality: {q}".format(
                met=metric_accuracy_count, total=total_metrics, q=quality,
            ),
            actor="EvaluationEngine",
        )

        return evaluation

    def get_history(self, decision_title: str) -> List[bool]:
        """Dapatkan history untuk satu tipe keputusan."""
        return self._history.get(decision_title, [])
