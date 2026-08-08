# Operational Readiness API - WP-47
# IP-3.2-005 (AO-3.2-001 / ED-3.2-005)
#
# Fasad read-only dari penilaian kesiapan operasional. Menyatukan agregasi,
# koordinasi-cerdas, penilaian risiko, rekomendasi, dan penjelasan menjadi satu
# antarmuka. Murni baca: TIDAK mengubah runtime, TIDAK mengeksekusi, TIDAK
# mengubah governance/policy, TIDAK memilih tindakan final.
# Deterministic.

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from sam.autonomy_runtime.operational_readiness.models import (
    OperationalReadiness,
    ReadinessInput,
)
from sam.autonomy_runtime.operational_readiness.aggregation import (
    ReadinessAggregationEngine,
)
from sam.autonomy_runtime.operational_readiness.coordination_intelligence import (
    AutonomousCoordinationIntelligence,
    CoordinationIntelligence,
)
from sam.autonomy_runtime.operational_readiness.risk import (
    OperationalRiskAssessor,
    OperationalRiskReport,
)
from sam.autonomy_runtime.operational_readiness.recommendation import (
    ReadinessRecommendation,
    ReadinessRecommender,
)
from sam.autonomy_runtime.operational_readiness.explainability import (
    ReadinessExplanation,
    ReadinessExplainer,
)


@dataclass(frozen=True)
class ReadinessSummary:
    """Ringkasan status kesiapan operasional (immutable)."""

    readiness_id: str
    overall_level: str
    overall_score: float
    ready: bool
    blocker_count: int
    top_risks: Tuple[str, ...]
    input_count: int
    is_proposal_only: bool = True

    def as_dict(self) -> Dict[str, Any]:
        return {
            "readiness_id": self.readiness_id,
            "overall_level": self.overall_level,
            "overall_score": self.overall_score,
            "ready": self.ready,
            "blocker_count": self.blocker_count,
            "top_risks": list(self.top_risks),
            "input_count": self.input_count,
            "is_proposal_only": self.is_proposal_only,
        }


class OperationalReadinessAPI:
    """Antarmuka read-only penilaian kesiapan operasional."""

    def __init__(
        self,
        engine: Optional[ReadinessAggregationEngine] = None,
        intelligence: Optional[AutonomousCoordinationIntelligence] = None,
        risk: Optional[OperationalRiskAssessor] = None,
        recommender: Optional[ReadinessRecommender] = None,
        explainer: Optional[ReadinessExplainer] = None,
    ):
        self._engine = engine or ReadinessAggregationEngine()
        self._intelligence = intelligence or AutonomousCoordinationIntelligence()
        self._risk = risk or OperationalRiskAssessor()
        self._recommender = recommender or ReadinessRecommender()
        self._explainer = explainer or ReadinessExplainer()

    def assess(
        self,
        inputs: Tuple[ReadinessInput, ...],
        readiness_id: str = "",
        created_at: str = "",
    ) -> OperationalReadiness:
        """Agregasi masukan menjadi penilaian kesiapan (read-only)."""
        return self._engine.build_readiness(inputs, readiness_id, created_at)

    def coordinate(self, readiness: OperationalReadiness) -> CoordinationIntelligence:
        """Evaluasi konsistensi antar penilaian (read-only)."""
        return self._intelligence.analyze(readiness)

    def risk(self, readiness: OperationalReadiness) -> OperationalRiskReport:
        """Penilaian risiko operasional (read-only)."""
        return self._risk.assess(readiness)

    def recommend(
        self,
        readiness: OperationalReadiness,
        risk_report: Optional[OperationalRiskReport] = None,
    ) -> ReadinessRecommendation:
        """Prioritas proposal operasional (proposal-only)."""
        return self._recommender.recommend(readiness, risk_report)

    def explain(
        self,
        readiness: OperationalReadiness,
        coordination: Optional[CoordinationIntelligence] = None,
        risk_report: Optional[OperationalRiskReport] = None,
    ) -> ReadinessExplanation:
        """Penjelasan kesimpulan kesiapan (read-only)."""
        return self._explainer.explain(readiness, coordination, risk_report)

    def summarize(self, readiness: OperationalReadiness) -> ReadinessSummary:
        """Ringkasan status kesiapan (read-only)."""
        return ReadinessSummary(
            readiness_id=readiness.readiness_id,
            overall_level=readiness.overall_level,
            overall_score=readiness.overall_score,
            ready=readiness.ready,
            blocker_count=len(readiness.blockers),
            top_risks=readiness.top_risks,
            input_count=readiness.input_count(),
            is_proposal_only=readiness.is_proposal_only,
        )

    def full_assessment(
        self,
        inputs: Tuple[ReadinessInput, ...],
        readiness_id: str = "",
        created_at: str = "",
    ) -> Dict[str, Any]:
        """Satu panggilan: assess + coordinate + risk + recommend + explain.

        Return dict lengkap (immutable snapshot). Ini masih read-only: tidak
        ada aksi apapun yang diambil; seluruh output siap dikonsumsi mekanisme
        governance yang lebih tinggi.
        """
        readiness = self.assess(inputs, readiness_id, created_at)
        coordination = self.coordinate(readiness)
        risk_report = self.risk(readiness)
        recommendation = self.recommend(readiness, risk_report)
        explanation = self.explain(readiness, coordination, risk_report)
        return {
            "readiness": readiness.as_dict(),
            "coordination": coordination.as_dict(),
            "risk": risk_report.as_dict(),
            "recommendation": recommendation.as_dict(),
            "explanation": explanation.as_dict(),
            "summary": self.summarize(readiness).as_dict(),
        }
