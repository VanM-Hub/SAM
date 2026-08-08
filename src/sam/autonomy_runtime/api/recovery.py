# Recovery API - WP-27
# IP-3.2-003 (AO-3.2-001 / ED-3.2-003)
#
# Read-only facade untuk strategi recovery. Runtime boleh analyze(),
# recover_plan() (membangun proposal), recommend() - TIDAK pernah mengeksekusi
# recovery. Seluruh output = deterministic proposal.

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from sam.autonomy_runtime.recovery.models import RecoveryContext
from sam.autonomy_runtime.recovery.failure_analysis import (
    FailureAnalysis,
    FailureAnalyzer,
)
from sam.autonomy_runtime.recovery.strategy import (
    RecoveryStrategy,
    RecoveryStrategyEngine,
)
from sam.autonomy_runtime.recovery.impact import (
    RecoveryImpactAnalyzer,
    RecoveryImpactReport,
)
from sam.autonomy_runtime.recovery.recommendation import (
    RecoveryRecommendation,
    RecoveryRecommender,
)
from sam.autonomy_runtime.healing.models import SelfHealingPlan
from sam.autonomy_runtime.healing.planner import SelfHealingPlanner


@dataclass(frozen=True)
class RecoverySummary:
    """Ringkasan read-only hasil analisis + strategi + rekomendasi."""

    state_id: str
    failure_count: int
    overall_severity: int
    strategy_count: int
    preferred_strategy: str
    overall_risk: str
    is_proposal_only: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "state_id": self.state_id,
            "failure_count": self.failure_count,
            "overall_severity": self.overall_severity,
            "strategy_count": self.strategy_count,
            "preferred_strategy": self.preferred_strategy,
            "overall_risk": self.overall_risk,
            "is_proposal_only": self.is_proposal_only,
            "metadata": dict(self.metadata),
        }


class RecoveryAPI:
    """Fasad read-only untuk strategic recovery (IP-3.2-003).

    Semua method murni analisis/proposal: tidak mengubah Runtime, Mission,
    Workflow, Policy, Governance, tidak menjalankan rollback/restart/self-heal.
    """

    def __init__(self):
        self._analyzer = FailureAnalyzer()
        self._strategy = RecoveryStrategyEngine()
        self._impact = RecoveryImpactAnalyzer()
        self._planner = SelfHealingPlanner()
        self._recommender = RecoveryRecommender()

    def analyze(
        self,
        failure_classification,
        context: RecoveryContext,
        created_at: str = "",
    ) -> FailureAnalysis:
        """Analisis kegagalan (deterministik, read-only)."""
        return self._analyzer.analyze(
            failure_classification, context, created_at=created_at
        )

    def recover_plan(
        self,
        failure_analysis: FailureAnalysis,
        context: RecoveryContext,
        created_at: str = "",
    ) -> "Tuple[RecoveryStrategy, SelfHealingPlan, RecoveryImpactReport]":
        """Membangun strategi + self-healing plan + impact (proposal only)."""
        strategy = self._strategy.build_strategy(
            failure_analysis, context, created_at=created_at
        )
        plan = self._planner.build_plan(strategy, context)
        impact = self._impact.analyze(strategy, plan, context)
        return strategy, plan, impact

    def recommend(
        self,
        failure_analysis: FailureAnalysis,
        context: RecoveryContext,
        strategies: Tuple[RecoveryStrategy, ...],
    ) -> RecoveryRecommendation:
        """Rekomendasi alternatif recovery berbasis trust (proposal only)."""
        return self._recommender.recommend(failure_analysis, context, strategies)

    def summarize(
        self,
        analysis: FailureAnalysis,
        strategies: Tuple[RecoveryStrategy, ...],
        recommendation: RecoveryRecommendation,
        impact: Optional[RecoveryImpactReport] = None,
    ) -> RecoverySummary:
        """Ringkasan read-only dari pipeline recovery."""
        preferred = recommendation.preferred
        return RecoverySummary(
            state_id=analysis.state_id,
            failure_count=analysis.failure_count(),
            overall_severity=analysis.overall_severity,
            strategy_count=len(strategies),
            preferred_strategy=preferred,
            overall_risk=impact.overall_risk if impact else "none",
            is_proposal_only=True,
            metadata={"deterministic": True},
        )
