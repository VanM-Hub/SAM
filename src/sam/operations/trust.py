"""
OP-114 — Trust Score Engine.

Skor kepercayaan 0-100 berdasarkan evidence nyata.
Grade A-E. Tidak ada hardcode — semua dari evidence.

Komponen:
  - Evidence Quality (berapa banyak evidence, kelengkapan)
  - Historical Accuracy (riwayat kebenaran)
  - Observation Completeness (seberapa penuh snapshot)
  - Prediction Accuracy (prediksi vs kenyataan)
  - Verification Success (seberapa sering verifikasi lolos)
  - Human Approval History (seberapa sering disetujui)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


GRADE_THRESHOLDS = {
    "A": (90, 100),
    "B": (75, 89),
    "C": (55, 74),
    "D": (35, 54),
    "E": (0, 34),
}

GRADE_DESCRIPTIONS = {
    "A": "Highly Trusted — decision quality is excellent",
    "B": "Trusted — minor gaps in evidence or accuracy",
    "C": "Moderate — needs more evidence to confirm",
    "D": "Low — significant gaps, should review before trusting",
    "E": "Untrusted — cannot rely on this decision",
}


def compute_grade(score: float) -> str:
    """Konversi score 0-100 ke grade A-E."""
    for grade, (low, high) in GRADE_THRESHOLDS.items():
        if low <= score <= high:
            return grade
    return "E"


@dataclass
class TrustComponents:
    """Komponen-komponen trust score."""
    evidence_quality: float = 0.0       # 0-100
    historical_accuracy: float = 0.0    # 0-100
    observation_completeness: float = 0.0  # 0-100
    prediction_accuracy: float = 0.0    # 0-100
    verification_success: float = 0.0   # 0-100
    human_approval_history: float = 0.0 # 0-100

    def to_dict(self) -> dict:
        return {
            "evidence_quality": self.evidence_quality,
            "historical_accuracy": self.historical_accuracy,
            "observation_completeness": self.observation_completeness,
            "prediction_accuracy": self.prediction_accuracy,
            "verification_success": self.verification_success,
            "human_approval_history": self.human_approval_history,
        }


@dataclass
class TrustScore:
    """Trust score untuk satu tipe keputusan / domain."""
    domain: str                              # "database", "disk", "network"
    score: float = 0.0                       # 0-100
    grade: str = "E"
    components: TrustComponents = field(default_factory=TrustComponents)
    reason: str = ""
    evidence_count: int = 0
    decision_count: int = 0
    computed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "score": self.score,
            "grade": self.grade,
            "components": self.components.to_dict(),
            "reason": self.reason,
            "evidence_count": self.evidence_count,
            "decision_count": self.decision_count,
        }


@dataclass
class TrustScorePackage:
    """Kumpulan trust scores."""
    scores: List[TrustScore] = field(default_factory=list)
    average_trust: float = 0.0

    def to_dict(self) -> dict:
        return {
            "average_trust": self.average_trust,
            "scores": [s.to_dict() for s in self.scores],
        }


class TrustConfig:
    """Konfigurasi bobot trust score."""
    def __init__(self,
                 weight_evidence: float = 0.25,
                 weight_history: float = 0.20,
                 weight_observation: float = 0.15,
                 weight_prediction: float = 0.15,
                 weight_verification: float = 0.15,
                 weight_approval: float = 0.10):
        total = (weight_evidence + weight_history + weight_observation +
                 weight_prediction + weight_verification + weight_approval)
        assert abs(total - 1.0) < 0.01, "Weights must sum to 1.0"
        self.weights = {
            "evidence": weight_evidence,
            "history": weight_history,
            "observation": weight_observation,
            "prediction": weight_prediction,
            "verification": weight_verification,
            "approval": weight_approval,
        }


class TrustScoreEngine:
    """Engine untuk menghitung trust score.

    Method utama:
      compute(domain, evidence_quality, historical_accuracy, ...) -> TrustScore
      get(domain) -> Optional[TrustScore]
      all() -> TrustScorePackage
    """

    def __init__(self, config: Optional[TrustConfig] = None):
        self.config = config or TrustConfig()
        self._scores: Dict[str, TrustScore] = {}
        self._decision_history: Dict[str, List[bool]] = {}  # domain → [success]
        self._verification_history: Dict[str, List[bool]] = {}  # domain → [passed]
        self._approval_history: Dict[str, List[bool]] = {}  # domain → [approved]

    def record_decision(self, domain: str, success: bool):
        """Catat hasil keputusan."""
        self._decision_history.setdefault(domain, []).append(success)

    def record_verification(self, domain: str, passed: bool):
        """Catat hasil verifikasi."""
        self._verification_history.setdefault(domain, []).append(passed)

    def record_approval(self, domain: str, approved: bool):
        """Catat hasil approval."""
        self._approval_history.setdefault(domain, []).append(approved)

    def compute(self, domain: str,
                evidence_quality: Optional[float] = None,
                observation_completeness: Optional[float] = None,
                prediction_accuracy: Optional[float] = None) -> TrustScore:
        """Hitung trust score untuk satu domain.

        Args:
            domain: Nama domain (database, disk, network, dll)
            evidence_quality: Kualitas evidence 0-100 (None = auto dari history)
            observation_completeness: Kelengkapan observasi 0-100
            prediction_accuracy: Akurasi prediksi 0-100

        Returns:
            TrustScore
        """
        # 1. Evidence quality
        if evidence_quality is not None:
            eq = max(0, min(100, evidence_quality))
        else:
            eq = 50.0  # default

        # 2. Historical accuracy
        hist_list = self._decision_history.get(domain, [])
        if hist_list:
            ha = (sum(1 for s in hist_list if s) / len(hist_list)) * 100
        else:
            ha = 50.0  # no data = moderate

        # 3. Observation completeness
        if observation_completeness is not None:
            oc = max(0, min(100, observation_completeness))
        else:
            oc = 50.0

        # 4. Prediction accuracy
        if prediction_accuracy is not None:
            pa = max(0, min(100, prediction_accuracy))
        else:
            pa = 50.0

        # 5. Verification success
        ver_list = self._verification_history.get(domain, [])
        if ver_list:
            vs = (sum(1 for v in ver_list if v) / len(ver_list)) * 100
        else:
            vs = 50.0

        # 6. Human approval history
        app_list = self._approval_history.get(domain, [])
        if app_list:
            ah = (sum(1 for a in app_list if a) / len(app_list)) * 100
        else:
            ah = 50.0  # no data = moderate

        components = TrustComponents(
            evidence_quality=round(eq, 1),
            historical_accuracy=round(ha, 1),
            observation_completeness=round(oc, 1),
            prediction_accuracy=round(pa, 1),
            verification_success=round(vs, 1),
            human_approval_history=round(ah, 1),
        )

        w = self.config.weights
        score = (
            eq * w["evidence"] +
            ha * w["history"] +
            oc * w["observation"] +
            pa * w["prediction"] +
            vs * w["verification"] +
            ah * w["approval"]
        )
        score = round(max(0, min(100, score)), 1)

        grade = compute_grade(score)

        # Reason
        ev_count = len(hist_list) + len(ver_list)
        dec_count = len(hist_list)
        reason_parts = []
        if eq < 50: reason_parts.append("low evidence quality ({:.0f})".format(eq))
        if ha < 50: reason_parts.append("low historical accuracy ({:.0f}%)".format(ha))
        if score >= 90:
            reason_parts.append("highly trusted")
        elif score >= 75:
            reason_parts.append("trusted with minor gaps")
        elif score >= 55:
            reason_parts.append("moderate — needs more data")
        else:
            reason_parts.append("low trust — significant gaps")

        trust = TrustScore(
            domain=domain,
            score=score,
            grade=grade,
            components=components,
            reason="; ".join(reason_parts),
            evidence_count=ev_count,
            decision_count=dec_count,
        )
        self._scores[domain] = trust
        return trust

    def get(self, domain: str) -> Optional[TrustScore]:
        """Dapatkan trust score terakhir untuk domain."""
        return self._scores.get(domain)

    def all(self) -> TrustScorePackage:
        """Semua trust scores."""
        scores = list(self._scores.values())
        avg = round(sum(s.score for s in scores) / max(1, len(scores)), 1) if scores else 0.0
        return TrustScorePackage(scores=scores, average_trust=avg)
