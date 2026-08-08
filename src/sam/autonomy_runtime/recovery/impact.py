# Recovery Impact Analyzer - WP-25
# IP-3.2-003 (AO-3.2-001 / ED-3.2-003)
#
# Dampak, risiko, dependency, readiness pasca-recovery. Proposal only.
# Menganalisis apa dampak yang akan timbul JIKA strategi dijalankan - tanpa
# menjalankan apa pun.

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from sam.autonomy_runtime.recovery.models import RecoveryContext
from sam.autonomy_runtime.recovery.strategy import RecoveryStrategy
from sam.autonomy_runtime.recovery.failure_analysis import FailureAnalysis
from sam.autonomy_runtime.healing.models import SelfHealingPlan

# Tingkat risiko: lebih tinggi = lebih berisiko
_RISK_LEVEL = {"low": 1, "medium": 2, "high": 3}

# Risiko per jenis strategi (heuristik deterministik)
_STRATEGY_RISK = {
    "recover_restore": "medium",
    "recover_replace": "high",
    "recover_retry": "low",
    "recover_rebalance": "medium",
    "recover_wait": "low",
    "recover_replicate": "medium",
}


@dataclass(frozen=True)
class ImpactItem:
    """Satu item dampak dari penerapan strategi."""

    target: str
    action: str
    impact: str  # deskripsi dampak
    risk: str  # low | medium | high
    affected_dependents: Tuple[str, ...] = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "action": self.action,
            "impact": self.impact,
            "risk": self.risk,
            "affected_dependents": list(self.affected_dependents),
        }


@dataclass(frozen=True)
class RecoveryImpactReport:
    """Laporan dampak recovery - immutable, proposal-only."""

    report_id: str
    state_id: str
    overall_risk: str  # low | medium | high
    risk_score: int
    items: Tuple[ImpactItem, ...] = ()
    post_recovery_readiness: str = "unknown"
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "state_id": self.state_id,
            "overall_risk": self.overall_risk,
            "risk_score": self.risk_score,
            "items": [i.as_dict() for i in self.items],
            "post_recovery_readiness": self.post_recovery_readiness,
            "summary": self.summary,
            "metadata": dict(self.metadata),
        }

    def item_count(self) -> int:
        return len(self.items)


class RecoveryImpactAnalyzer:
    """Menganalisis dampak recovery (dari strategi + healing plan).

    Deterministik: menilai risiko tiap tindakan, dependency yang terpengaruh
    (dependents), dan readiness pasca-recovery. Murni simulasi/estimasi -
    tidak menjalankan recovery.
    """

    def analyze(
        self,
        strategy: RecoveryStrategy,
        plan: SelfHealingPlan,
        context: RecoveryContext,
        report_id: str = "",
    ) -> RecoveryImpactReport:
        items: List[ImpactItem] = []
        children = _child_map(context)

        for step in plan.steps:
            risk = _STRATEGY_RISK.get(step.action, "medium")
            dependents = tuple(sorted(children.get(step.target, ())))
            impact = self._impact_text(step.target, step.action, risk, dependents)
            items.append(
                ImpactItem(
                    target=step.target,
                    action=step.action,
                    impact=impact,
                    risk=risk,
                    affected_dependents=dependents,
                )
            )

        items_tuple = tuple(items)
        overall_risk, risk_score = _overall_risk(items_tuple)
        post = self._post_readiness(strategy, context)
        report_id = report_id or self._stable_id(context.state_id)
        return RecoveryImpactReport(
            report_id=report_id,
            state_id=context.state_id,
            overall_risk=overall_risk,
            risk_score=risk_score,
            items=items_tuple,
            post_recovery_readiness=post,
            summary=(
                "Estimated impact of recovery strategy {}; simulated, "
                "no execution".format(strategy.strategy_id)
            ),
            metadata={"deterministic": True},
        )

    @staticmethod
    def _impact_text(
        target: str, action: str, risk: str, dependents: Tuple[str, ...]
    ) -> str:
        base = "{} via {} (risk {})".format(target, action.strip("recover_"), risk)
        if dependents:
            return "{}; affects dependents {}".format(base, ", ".join(dependents))
        return base

    @staticmethod
    def _post_readiness(
        strategy: RecoveryStrategy, context: RecoveryContext
    ) -> str:
        """Estimasi readiness pasca-recovery (deterministik heuristik)."""
        if not strategy.actions:
            return "unknown"
        # jika semua target strategi selesai (proposal) dan tidak ada strategi
        # berisiko tinggi, readiness diproyeksi meningkat ke degraded/healthy
        high_risk = any(
            _STRATEGY_RISK.get(a.action, "medium") == "high"
            for a in strategy.actions
        )
        if high_risk:
            return "degraded"
        if strategy.confidence >= 80:
            return "ready"
        return "degraded"

    @staticmethod
    def _stable_id(seed: str) -> str:
        import hashlib

        return "ri-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]


def _child_map(context: RecoveryContext) -> Dict[str, Tuple[str, ...]]:
    """Peta komponen -> dependents (komponen yang bergantung padanya)."""
    children: Dict[str, list] = {}
    for src, dst in context.dependency_edges:
        children.setdefault(src, []).append(dst)
    return {k: tuple(v) for k, v in children.items()}


def _overall_risk(items: Tuple[ImpactItem, ...]) -> "tuple[str, int]":
    """Risiko menyeluruh = risiko tertinggi di antara item."""
    if not items:
        return "low", 1
    worst = max(_RISK_LEVEL.get(i.risk, 1) for i in items)
    name = {1: "low", 2: "medium", 3: "high"}[worst]
    return name, worst
