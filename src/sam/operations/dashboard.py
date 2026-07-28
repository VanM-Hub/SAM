"""
OP-116 — Trust Dashboard Model.

DTO-only. Tidak ada renderer, tidak ada UI.
Model untuk menampilkan decision health secara agregat.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class TrustDashboardDTO:
    """DTO untuk trust dashboard.

    Hanya data — tidak ada renderer.
    """
    # Decision Health
    decision_accuracy: float = 0.0           # 0-100%
    prediction_accuracy: float = 0.0         # 0-100%
    approval_rate: float = 0.0               # 0-100%
    rollback_rate: float = 0.0               # 0-100%
    verification_success_rate: float = 0.0   # 0-100%

    # Quality Metrics
    false_positive: int = 0
    false_negative: int = 0
    pending_decisions: int = 0

    # Aggregate
    average_confidence: float = 0.0          # 0-100%
    average_trust: float = 0.0               # 0-100 (trust score)
    grade: str = "E"

    # Meta
    total_decisions: int = 0
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "decision_accuracy": self.decision_accuracy,
            "prediction_accuracy": self.prediction_accuracy,
            "approval_rate": self.approval_rate,
            "rollback_rate": self.rollback_rate,
            "verification_success_rate": self.verification_success_rate,
            "false_positive": self.false_positive,
            "false_negative": self.false_negative,
            "pending_decisions": self.pending_decisions,
            "average_confidence": self.average_confidence,
            "average_trust": self.average_trust,
            "grade": self.grade,
            "total_decisions": self.total_decisions,
        }
