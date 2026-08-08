# Federation Operational API - WP-37
# IP-3.4-004 (AO-3.4-001, paket keempat - Federation Operational Coordination
# & Ecosystem Readiness)
#
# Facade read-only untuk Operational Coordination & Ecosystem Readiness.
#
# Guardrail IP-3.4-004:
#   Read-only operational API (OR-10)
#   Readiness != Execution (OR-01)
#   Recommendation != Command (OR-03)
#
# API hanya memapar: readiness assessment, coordination insight, federation
# health, federation recommendation, operational explanation.
# TIDAK ada connect/execute/authorize/failover/load-balance/schedule.

from typing import Any, Dict, Optional, Tuple

from sam.citizen.federation.aggregation import (
    FederationReadinessAggregate,
    FederationReadinessAggregator,
)
from sam.citizen.federation.coordination_intelligence import (
    CoordinationInsight,
    CoordinationIntelligence,
)
from sam.citizen.federation.explainability import (
    CoordinationExplanation,
    FederationOperationalExplainer,
    ReadinessExplanation,
)
from sam.citizen.federation.operational_readiness import (
    FederationOperationalModel,
    FederationReadiness,
)
from sam.citizen.federation.recommendation import (
    CoordinationRecommendationResult,
    CoordinationRecommendationEngine,
)
from sam.citizen.federation.risk import (
    FederationRiskAssessment,
    FederationRiskAssessor,
)


class FederationOperationalAPI:
    """Facade read-only untuk kesiapan operasional & koordinasi Federation.

    Seluruh method assessment/advisory. Tidak ada method yang mengubah
    state, menjalankan workflow, memilih leader, men-schedule, failover,
    load balancing, atau mengubah registry/trust/governance.
    """

    def __init__(
        self,
        model=None,
        aggregator=None,
        coordination=None,
        risk_assessor=None,
        recommender=None,
        explainer=None,
    ) -> None:
        self._model = model or FederationOperationalModel()
        self._aggregator = aggregator or FederationReadinessAggregator()
        self._coordination = coordination or CoordinationIntelligence()
        self._risk_assessor = risk_assessor or FederationRiskAssessor()
        self._recommender = recommender or CoordinationRecommendationEngine()
        self._explainer = explainer or FederationOperationalExplainer()

    # --- readiness assessment (OR-01: assessment, bukan eksekusi) ---

    def assess_readiness(
        self,
        member_id: str,
        scores: Dict[str, float],
        evidence: Optional[Tuple[str, ...]] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> FederationReadiness:
        return self._model.assess(member_id, scores, evidence, weights)

    def aggregate_readiness(
        self,
        members: Tuple[FederationReadiness, ...],
    ) -> FederationReadinessAggregate:
        return self._aggregator.aggregate(members)

    # --- coordination insight (OR-02: insight, bukan orchestration) ---

    def coordination_insights(
        self,
        aggregate: FederationReadinessAggregate,
    ) -> Tuple[CoordinationInsight, ...]:
        return self._coordination.analyze(aggregate)

    # --- federation health (OR-05: observational, bukan kontrol runtime) ---

    def federation_health(
        self,
        aggregate: FederationReadinessAggregate,
    ) -> Dict[str, Any]:
        """Pengamatan kesehatan kolektif Federation (observasional)."""
        return {
            "overall": aggregate.overall,
            "level": aggregate.level,
            "member_count": len(aggregate.members),
            "level_distribution": dict(aggregate.level_distribution or {}),
            "ready": bool(aggregate.level == "ready"),
        }

    # --- federation risk (OR-04: assessment, bukan authority) ---

    def federation_risk(
        self,
        aggregate: FederationReadinessAggregate,
    ) -> FederationRiskAssessment:
        return self._risk_assessor.assess(aggregate)

    # --- federation recommendation (OR-03: suggestion, bukan command) ---

    def recommend_coordination(
        self,
        aggregate: FederationReadinessAggregate,
    ) -> CoordinationRecommendationResult:
        risk = self._risk_assessor.assess(aggregate)
        insights = self._coordination.analyze(aggregate)
        return self._recommender.recommend(aggregate, risk, insights)

    # --- operational explanation ---

    def explain_readiness(
        self,
        aggregate: FederationReadinessAggregate,
    ) -> ReadinessExplanation:
        return self._explainer.explain_aggregate(aggregate)

    def explain_coordination(
        self,
        aggregate: FederationReadinessAggregate,
    ) -> Tuple[CoordinationExplanation, ...]:
        result = self.recommend_coordination(aggregate)
        return tuple(
            self._explainer.explain_recommendation(r)
            for r in result.recommendations)

    # --- read-only enforcement helpers (untuk test) ---

    def allowed_actions(self) -> Tuple[str, ...]:
        """Daftar tindakan read-only yang diizinkan (assessment/advisory)."""
        return ("assess_readiness", "aggregate_readiness",
                "coordination_insights", "federation_health",
                "federation_risk", "recommend_coordination",
                "explain_readiness", "explain_coordination")

    def has_authority_action(self) -> bool:
        """False: API tidak memiliki aksi otoritas/eksekusi/koordinasi nyata."""
        forbidden = ("connect", "execute", "authorize", "approve",
                     "failover", "load_balance", "schedule", "select_leader",
                     "activate", "sync_state", "run_workflow")
        return any(hasattr(self, name) for name in forbidden)
