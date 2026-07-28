"""
Operational Benchmark — perbandingan keputusan vs hasil nyata.

Hitung akurasi statistik murni.
Tidak ada machine learning atau AI yang belajar sendiri.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime


@dataclass
class DecisionReportRow:
    """Satu baris dalam decision report."""
    recommendation: str
    expected_outcome: str
    actual_outcome: str
    mismatch: bool
    confidence: float
    evidence_count: int
    success: bool

    def to_dict(self) -> dict:
        return {
            "recommendation": self.recommendation[:40],
            "expected": self.expected_outcome[:40],
            "actual": self.actual_outcome[:40],
            "mismatch": self.mismatch,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "success": self.success,
        }


@dataclass
class DecisionReport:
    """Laporan perbandingan keputusan vs hasil nyata."""
    total_decisions: int = 0
    correct: int = 0
    incorrect: int = 0
    uncertain: int = 0
    needs_human: int = 0

    # Accuracy metrics
    average_confidence: float = 0.0
    average_evidence: float = 0.0
    accuracy_trend: str = ""            # "improving", "stable", "degrading", "insufficient_data"

    # Detailed metrics
    prediction_accuracy: float = 0.0    # Prediction vs actual outcome
    decision_accuracy: float = 0.0      # Decision accuracy
    recommendation_usefulness: float = 0.0  # Seberapa sering rekomendasi dipakai

    # FP/FN
    false_positive: int = 0
    false_negative: int = 0

    # Rows
    rows: List[DecisionReportRow] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_text(self) -> str:
        lines = [
            "=== Decision Report ===",
            "Total decisions: {total} | Correct: {correct} | Incorrect: {incorrect} | Uncertain: {uncertain}".format(
                total=self.total_decisions, correct=self.correct,
                incorrect=self.incorrect, uncertain=self.uncertain,
            ),
            "Needs human: {human}".format(human=self.needs_human),
            "Accuracy: {acc:.1f}% (prediction) | {dacc:.1f}% (decision)".format(
                acc=self.prediction_accuracy * 100,
                dacc=self.decision_accuracy * 100,
            ),
            "Recommendation usefulness: {useful:.0f}%".format(
                useful=self.recommendation_usefulness * 100,
            ),
            "FP: {fp} | FN: {fn} | Avg confidence: {conf:.0f}% | Avg evidence: {ev:.1f}".format(
                fp=self.false_positive, fn=self.false_negative,
                conf=self.average_confidence * 100, ev=self.average_evidence,
            ),
            "Trend: {trend}".format(trend=self.accuracy_trend),
        ]
        if self.rows:
            lines.append("")
            lines.append("Recent decisions ({count}):".format(count=len(self.rows)))
            for row in self.rows[-5:]:  # Last 5
                marker = "✗" if row.mismatch else "✓"
                lines.append("  {marker} {rec} ({conf:.0f}%)".format(
                    marker=marker, rec=row.recommendation[:30], conf=row.confidence * 100,
                ))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "total_decisions": self.total_decisions,
            "correct": self.correct,
            "incorrect": self.incorrect,
            "uncertain": self.uncertain,
            "needs_human": self.needs_human,
            "prediction_accuracy": self.prediction_accuracy,
            "decision_accuracy": self.decision_accuracy,
            "recommendation_usefulness": self.recommendation_usefulness,
            "false_positive": self.false_positive,
            "false_negative": self.false_negative,
            "average_confidence": self.average_confidence,
            "average_evidence": self.average_evidence,
            "accuracy_trend": self.accuracy_trend,
            "row_count": len(self.rows),
        }


class BenchmarkEngine:
    """Engine untuk membandingkan keputusan vs hasil nyata.

    Method utama:
      record_outcome(proposal, expected, actual, success) — catat satu outcome
      generate_report() -> DecisionReport — hasilkan laporan
      get_prediction_accuracy(decision_title) -> float — akurasi untuk satu keputusan

    Semua statistik murni — tidak ada ML.
    """

    def __init__(self):
        self._records: List[Tuple[str, str, str, float, int, bool]] = []  # (title, expected, actual, conf, ev_count, success)
        self._history: Dict[str, List[bool]] = {}  # trend tracking

    def record_outcome(self, proposal_title: str,
                       expected_outcome: str,
                       actual_outcome: str,
                       confidence: float,
                       evidence_count: int,
                       success: bool) -> DecisionReportRow:
        """Catat satu outcome perbandingan.

        Args:
            proposal_title: Judul proposal/rekomendasi
            expected_outcome: Expected outcome
            actual_outcome: Actual outcome setelah eksekusi
            confidence: Confidence saat rekomendasi
            evidence_count: Evidence count
            success: Apakah eksekusi sukses

        Returns:
            DecisionReportRow
        """
        mismatch = expected_outcome.lower().strip() != actual_outcome.lower().strip()

        row = DecisionReportRow(
            recommendation=proposal_title,
            expected_outcome=expected_outcome,
            actual_outcome=actual_outcome,
            mismatch=mismatch,
            confidence=confidence,
            evidence_count=evidence_count,
            success=success,
        )
        self._records.append((proposal_title, expected_outcome, actual_outcome, confidence, evidence_count, success))
        self._history.setdefault(proposal_title, []).append(success)

        return row

    def generate_report(self) -> DecisionReport:
        """Hasilkan laporan komprehensif.

        Returns:
            DecisionReport — semua metrik.
        """
        if not self._records:
            return DecisionReport(
                accuracy_trend="insufficient_data",
            )

        total = len(self._records)
        correct = 0
        incorrect = 0
        uncertain = 0
        needs_human = 0
        false_positive = 0
        false_negative = 0
        total_confidence = 0.0
        total_evidence = 0.0
        successful_exec = 0
        rows = []

        for title, expected, actual, conf, ev_count, success in self._records:
            mismatch = expected.lower().strip() != actual.lower().strip()

            row = DecisionReportRow(
                recommendation=title,
                expected_outcome=expected,
                actual_outcome=actual,
                mismatch=mismatch,
                confidence=conf,
                evidence_count=ev_count,
                success=success,
            )
            rows.append(row)

            total_confidence += conf
            total_evidence += ev_count

            if mismatch:
                incorrect += 1
            else:
                correct += 1

            if success:
                successful_exec += 1

            # Low confidence = uncertain
            if conf < 0.3:
                uncertain += 1

            # Mismatch + expected bad = FP
            # Mismatch + expected good = FN
            if mismatch:
                if "fail" in expected.lower() or "unchanged" in expected.lower() or "worsen" in expected.lower():
                    false_positive += 1
                elif "success" in actual.lower() or "active" in actual.lower() or "freed" in actual.lower():
                    false_negative += 1

            # Needs human = low confidence + mismatch
            if conf < 0.3 or (mismatch and conf < 0.5):
                needs_human += 1

        # Decision accuracy
        decision_accuracy = correct / max(1, total)

        # Prediction accuracy
        prediction_accuracy = correct / max(1, total)

        # Recommendation usefulness
        recommendation_usefulness = successful_exec / max(1, total)

        # Trend — dari history
        trend = self._compute_trend()

        report = DecisionReport(
            total_decisions=total,
            correct=correct,
            incorrect=incorrect,
            uncertain=uncertain,
            needs_human=needs_human,
            average_confidence=round(total_confidence / max(1, total), 2),
            average_evidence=round(total_evidence / max(1, total), 1),
            accuracy_trend=trend,
            prediction_accuracy=round(prediction_accuracy, 2),
            decision_accuracy=round(decision_accuracy, 2),
            recommendation_usefulness=round(recommendation_usefulness, 2),
            false_positive=false_positive,
            false_negative=false_negative,
            rows=rows,
        )

        return report

    def get_prediction_accuracy(self, decision_title: str) -> float:
        """Akurasi untuk satu tipe keputusan tertentu."""
        records_for_title = [
            r for r in self._records if r[0].lower().strip() == decision_title.lower().strip()
        ]
        if not records_for_title:
            return 0.0
        correct = sum(1 for r in records_for_title if r[1].lower().strip() == r[2].lower().strip())
        return correct / len(records_for_title)

    def _compute_trend(self) -> str:
        """Compute accuracy trend from history."""
        if len(self._records) < 5:
            return "insufficient_data"

        # Split into first half vs second half
        mid = len(self._records) // 2
        first_half = self._records[:mid]
        second_half = self._records[mid:]

        first_accuracy = sum(
            1 for r in first_half if r[1].lower().strip() == r[2].lower().strip()
        ) / max(1, len(first_half))

        second_accuracy = sum(
            1 for r in second_half if r[1].lower().strip() == r[2].lower().strip()
        ) / max(1, len(second_half))

        if second_accuracy > first_accuracy + 0.1:
            return "improving"
        elif first_accuracy > second_accuracy + 0.1:
            return "degrading"
        else:
            return "stable"
