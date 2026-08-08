# Recovery Explainability - WP-28
# IP-3.2-003 (AO-3.2-001 / ED-3.2-003)
#
# Penjelasan mengapa strategi recovery dipilih. Proposal only.
# Runtime dapat menjelaskan proses pemilihan strategi secara deterministik &
# berbasis evidence - tanpa mengambil keputusan eksekusi.

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from sam.autonomy_runtime.recovery.models import RecoveryContext
from sam.autonomy_runtime.recovery.failure_analysis import FailureAnalysis
from sam.autonomy_runtime.recovery.strategy import RecoveryStrategy
from sam.autonomy_runtime.recovery.recommendation import RecoveryRecommendation
from sam.autonomy_runtime.recovery.impact import RecoveryImpactReport


@dataclass(frozen=True)
class RecoveryExplanationItem:
    """Penjelasan satu pilihan strategi."""

    strategy_id: str
    strategy: str
    target: str
    failure_class: str
    rationale: str
    evidence: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy": self.strategy,
            "target": self.target,
            "failure_class": self.failure_class,
            "rationale": self.rationale,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class RecoveryExplanation:
    """Penjelasan komprehensif mengapa strategi recovery dipilih."""

    explanation_id: str
    state_id: str
    basis: str
    items: Tuple[RecoveryExplanationItem, ...] = ()
    preferred_strategy: str = ""
    risk_note: str = ""
    is_proposal_only: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "state_id": self.state_id,
            "basis": self.basis,
            "items": [i.as_dict() for i in self.items],
            "preferred_strategy": self.preferred_strategy,
            "risk_note": self.risk_note,
            "is_proposal_only": self.is_proposal_only,
            "metadata": dict(self.metadata),
        }

    def item_count(self) -> int:
        return len(self.items)


class RecoveryExplainer:
    """Menjelaskan mengapa strategi recovery dipilih (deterministik)."""

    def explain(
        self,
        analysis: FailureAnalysis,
        strategy: RecoveryStrategy,
        recommendation: RecoveryRecommendation,
        impact: RecoveryImpactReport,
        context: RecoveryContext,
        explanation_id: str = "",
    ) -> RecoveryExplanation:
        items: List[RecoveryExplanationItem] = []
        fclass = {f.component: f.failure_class for f in analysis.failures}

        for action in strategy.actions:
            cls = fclass.get(action.target, "unknown")
            items.append(
                RecoveryExplanationItem(
                    strategy_id=strategy.strategy_id,
                    strategy=action.action,
                    target=action.target,
                    failure_class=cls,
                    rationale=action.rationale,
                    evidence=(cls, action.strategy),
                )
            )

        explanation_id = explanation_id or self._stable_id(context.state_id)
        return RecoveryExplanation(
            explanation_id=explanation_id,
            state_id=context.state_id,
            basis=(
                "Recovery selected based on failure analysis (evidence), "
                "readiness, and dependency impact; proposal only"
            ),
            items=tuple(items),
            preferred_strategy=recommendation.preferred,
            risk_note="Overall risk: {}".format(impact.overall_risk),
            is_proposal_only=True,
            metadata={"deterministic": True},
        )

    @staticmethod
    def _stable_id(seed: str) -> str:
        import hashlib

        return "re-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
