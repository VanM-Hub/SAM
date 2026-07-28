"""
OP-118 — Decision Quality Benchmark.

Benchmark kualitas keputusan — bukan performa.
Metrik: Accuracy, Precision, Recall, Consistency, Trust, Stability, Human Agreement, Verification Success, Recovery Success.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class QualityMetrics:
    """Satu set metrik kualitas."""
    accuracy: float = 0.0            # 0-100%
    precision: float = 0.0           # 0-100%
    recall: float = 0.0              # 0-100%
    consistency: float = 0.0         # 0-100%
    trust: float = 0.0               # 0-100%
    stability: float = 0.0           # 0-100%
    human_agreement: float = 0.0     # 0-100%
    verification_success: float = 0.0 # 0-100%
    recovery_success: float = 0.0    # 0-100%

    def to_dict(self) -> dict:
        return {
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "consistency": self.consistency,
            "trust": self.trust,
            "stability": self.stability,
            "human_agreement": self.human_agreement,
            "verification_success": self.verification_success,
            "recovery_success": self.recovery_success,
        }


@dataclass
class QualityReport:
    """Laporan benchmark kualitas."""
    metrics: QualityMetrics = field(default_factory=QualityMetrics)
    overall_quality: float = 0.0     # Rata-rata semua metrik
    grade: str = "E"
    total_decisions_included: int = 0
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "metrics": self.metrics.to_dict(),
            "overall_quality": self.overall_quality,
            "grade": self.grade,
            "total_decisions_included": self.total_decisions_included,
        }

    def to_text(self) -> str:
        m = self.metrics
        lines = [
            "=== Decision Quality Benchmark ===",
            "Overall quality: {:.1f}% — Grade {grade}".format(
                self.overall_quality, grade=self.grade),
            "",
            "  Accuracy:           {:.1f}%".format(m.accuracy),
            "  Precision:          {:.1f}%".format(m.precision),
            "  Recall:             {:.1f}%".format(m.recall),
            "  Consistency:        {:.1f}%".format(m.consistency),
            "  Trust:              {:.1f}%".format(m.trust),
            "  Stability:          {:.1f}%".format(m.stability),
            "  Human Agreement:    {:.1f}%".format(m.human_agreement),
            "  Verification:       {:.1f}%".format(m.verification_success),
            "  Recovery:           {:.1f}%".format(m.recovery_success),
            "",
            "Based on {} decisions.".format(self.total_decisions_included),
        ]
        return "\n".join(lines)


class QualityBenchmark:
    """Benchmark kualitas keputusan.

    Method:
      compute(benchmark_data) -> QualityReport
      to_text() -> str
    """

    def compute(self,
                accuracy: float = 0.0,
                precision: float = 0.0,
                recall: float = 0.0,
                consistency: float = 0.0,
                trust: float = 0.0,
                stability: float = 0.0,
                human_agreement: float = 0.0,
                verification_success: float = 0.0,
                recovery_success: float = 0.0,
                total_decisions: int = 0) -> QualityReport:
        """Hitung benchmark dari data yang sudah ada."""

        def clamp(v):
            return max(0, min(100, v))

        metrics = QualityMetrics(
            accuracy=clamp(accuracy),
            precision=clamp(precision),
            recall=clamp(recall),
            consistency=clamp(consistency),
            trust=clamp(trust),
            stability=clamp(stability),
            human_agreement=clamp(human_agreement),
            verification_success=clamp(verification_success),
            recovery_success=clamp(recovery_success),
        )

        overall = round((
            metrics.accuracy + metrics.precision + metrics.recall +
            metrics.consistency + metrics.trust + metrics.stability +
            metrics.human_agreement + metrics.verification_success +
            metrics.recovery_success
        ) / 9, 1)

        # Grade
        if overall >= 90:
            grade = "A"
        elif overall >= 75:
            grade = "B"
        elif overall >= 55:
            grade = "C"
        elif overall >= 35:
            grade = "D"
        else:
            grade = "E"

        return QualityReport(
            metrics=metrics,
            overall_quality=overall,
            grade=grade,
            total_decisions_included=total_decisions,
        )

    @classmethod
    def from_report_data(cls, accuracy: float, trust: float, consistency: float,
                         verification_success: float, total: int) -> QualityReport:
        """Buat benchmark dari data yang ada."""
        return cls().compute(
            accuracy=accuracy,
            precision=accuracy * 0.95,   # approximate
            recall=accuracy * 0.90,
            consistency=consistency,
            trust=trust,
            stability=consistency * 0.90,
            human_agreement=trust * 0.90,
            verification_success=verification_success,
            recovery_success=accuracy * 0.85,
            total_decisions=total,
        )
