# Recovery Recommendation - WP-26
# IP-3.2-003 (AO-3.2-001 / ED-3.2-003)
#
# Alternatif recovery dengan evidence & trust. Proposal only.
# Menyusun rekomendasi - bukan keputusan. Runtime menyarankan, tidak memilih
# eksekusi.

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from sam.autonomy_runtime.recovery.models import RecoveryContext
from sam.autonomy_runtime.recovery.strategy import RecoveryStrategy, RecoveryStrategyEngine
from sam.autonomy_runtime.recovery.failure_analysis import FailureAnalysis
from sam.autonomy_runtime.recovery.impact import RecoveryImpactAnalyzer


@dataclass(frozen=True)
class RecoveryOption:
    """Satu alternatif recovery yang diusulkan."""

    strategy_id: str
    strategy: str  # nama strategi (recover_*)
    target_components: Tuple[str, ...] = ()
    confidence: int = 0  # 0..100
    trust_score: int = 0  # 0..100 (evidence + confidence)
    risk: str = "medium"
    rationale: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "strategy": self.strategy,
            "target_components": list(self.target_components),
            "confidence": self.confidence,
            "trust_score": self.trust_score,
            "risk": self.risk,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class RecoveryRecommendation:
    """Rekomendasi recovery - daftar alternatif + urutan preferensi."""

    recommendation_id: str
    state_id: str
    options: Tuple[RecoveryOption, ...] = ()
    preferred: str = ""  # strategy_id dari opsi paling dipercaya
    basis: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "state_id": self.state_id,
            "options": [o.as_dict() for o in self.options],
            "preferred": self.preferred,
            "basis": self.basis,
            "metadata": dict(self.metadata),
        }

    def option_count(self) -> int:
        return len(self.options)


class RecoveryRecommender:
    """Menyusun rekomendasi recovery berbasis evidence & trust.

    Deterministik: untuk setiap strategi alternatif yang layak, hitung
    trust_score = gabungan evidence (confidence) & risk; urutkan. Tidak
    memilih/menjalankan apa pun - hanya rekomendasi terurut.
    """

    def __init__(self):
        self._engine = RecoveryStrategyEngine()
        self._impact = RecoveryImpactAnalyzer()

    def recommend(
        self,
        failure_analysis: FailureAnalysis,
        context: RecoveryContext,
        strategies: Tuple[RecoveryStrategy, ...],
        recommendation_id: str = "",
    ) -> RecoveryRecommendation:
        options: List[RecoveryOption] = []
        for strat in strategies:
            trust = self._trust_score(strat)
            risk = self._risk_of(strat, context)
            options.append(
                RecoveryOption(
                    strategy_id=strat.strategy_id,
                    strategy=_primary_strategy(strat),
                    target_components=strat.target_components,
                    confidence=strat.confidence,
                    trust_score=trust,
                    risk=risk,
                    rationale=self._rationale(strat, risk),
                )
            )

        # urutkan: trust_score turun, lalu confidence turun, lalu id naik
        options.sort(key=lambda o: (-o.trust_score, -o.confidence, o.strategy_id))
        preferred = options[0].strategy_id if options else ""

        recommendation_id = recommendation_id or self._stable_id(context.state_id)
        return RecoveryRecommendation(
            recommendation_id=recommendation_id,
            state_id=context.state_id,
            options=tuple(options),
            preferred=preferred,
            basis=(
                "Recommended recovery options for state {} ranked by "
                "trust (evidence + confidence + risk); proposal only".format(
                    context.state_id
                )
            ),
            metadata={"deterministic": True},
        )

    def _trust_score(self, strat: RecoveryStrategy) -> int:
        """Trust = confidence + evidence coverage, diprioritaskan secara murni."""
        base_conf = strat.confidence
        # strategi dengan evidence lebih luas (lebih banyak komponen) lebih dipercaya
        evidence_count = len(strat.evidence_basis)
        trust = int(0.7 * base_conf + 0.3 * min(100, evidence_count * 20))
        return min(100, trust)

    def _risk_of(self, strat: RecoveryStrategy, context: RecoveryContext) -> str:
        report = self._impact.analyze(
            strat, _dummy_plan(strat, context), context
        )
        return report.overall_risk

    def _rationale(self, strat: RecoveryStrategy, risk: str) -> str:
        return (
            "Strategy {} with confidence {} and risk {}; "
            "recommended (proposal, no execution)".format(
                _primary_strategy(strat), strat.confidence, risk
            )
        )

    @staticmethod
    def _stable_id(seed: str) -> str:
        import hashlib

        return "rr-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]


def _primary_strategy(strat: RecoveryStrategy) -> str:
    """Nama strategi utama (dari action pertama)."""
    if strat.actions:
        return strat.actions[0].action
    return "none"


def _dummy_plan(strat: RecoveryStrategy, context: RecoveryContext):
    """Plan ringan untuk keperluan estimasi risk (read-only, bukan eksekusi)."""
    from sam.autonomy_runtime.healing.planner import SelfHealingPlanner

    return SelfHealingPlanner().build_plan(strat, context)
