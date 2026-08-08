# Recovery Strategy Engine - WP-23
# IP-3.2-003 (AO-3.2-001 / ED-3.2-003)
#
# RecoveryStrategy berdasarkan evidence & readiness. Proposal only.
# Strategic recovery: Runtime boleh memahami kegagalan & menyusun strategi,
# TIDAK boleh melakukan recovery konstitusional secara sepihak.

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from sam.autonomy_runtime.recovery.models import RecoveryContext
from sam.autonomy_runtime.recovery.failure_analysis import FailureAnalysis

# Taksonomi strategi recovery (strategic, bukan eksekusi)
_RESTORE = "recover_restore"
_REPLACE = "recover_replace"
_RETRY = "recover_retry"
_REBALANCE = "recover_rebalance"
_WAIT = "recover_wait"
_REPLICATE = "recover_replicate"
_NONE = "none"

# Pemetaan failure class -> strategi yang layak (deterministik, berbasis evidence)
_RECOMMENDED = {
    "connectivity_failure": (_REPLICATE, _RETRY),
    "dependency_failure": (_RESTORE, _RETRY),
    "configuration_error": (_REPLACE, _RESTORE),
    "resource_exhaustion": (_REBALANCE, _REPLICATE),
    "unavailable": (_REPLICATE, _REPLACE),
    "unknown": (_WAIT,),
    "none": (_NONE,),
}

# Kata kunci penilaian readiness/strategi


@dataclass(frozen=True)
class RecoverAction:
    """Satu tindakan strategi recovery (proposal, bukan eksekusi)."""

    action: str
    target: str
    strategy: str
    rationale: str
    sequence: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "target": self.target,
            "strategy": self.strategy,
            "rationale": self.rationale,
            "sequence": self.sequence,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RecoveryStrategy:
    """Strategi recovery yang diusulkan - immutable, proposal-only.

    Menyusun urutan tindakan recovery sebagai PROPOSAL. Tidak menjalankan
    apa pun terhadap runtime. Berbasis evidence (failure analysis) &
    readiness (ketersediaan komponen prasyarat).
    """

    strategy_id: str
    context: RecoveryContext
    target_components: Tuple[str, ...] = ()
    actions: Tuple[RecoverAction, ...] = ()
    readiness_gate: str = "none"  # readiness min yang harus dipenuhi
    evidence_basis: Tuple[str, ...] = ()
    confidence: int = 0  # 0..100 (proposal, bukan kepastian)
    summary: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "strategy_id": self.strategy_id,
            "target_components": list(self.target_components),
            "actions": [a.as_dict() for a in self.actions],
            "readiness_gate": self.readiness_gate,
            "evidence_basis": list(self.evidence_basis),
            "confidence": self.confidence,
            "summary": self.summary,
            "context": self.context.as_dict(),
            "metadata": dict(self.metadata),
        }

    def action_count(self) -> int:
        return len(self.actions)

    def is_proposal_only(self) -> bool:
        """Strategi ini murni proposal - semua tindakan ber-label recover_."""
        return all(a.action.startswith("recover_") for a in self.actions)


class RecoveryStrategyEngine:
    """Menyusun RecoveryStrategy dari failure analysis & recovery context.

    Deterministik: pilih strategi per komponen berdasarkan failure class
    (evidence), urutkan berdasarkan severity & dependency, dan nilai
    readiness gate. Tidak mengubah input, tidak mengeksekusi apa pun.
    """

    def build_strategy(
        self,
        failure_analysis: FailureAnalysis,
        context: RecoveryContext,
        strategy_id: str = "",
        created_at: str = "",
    ) -> RecoveryStrategy:
        """Menyusun strategi recovery (proposal) dari analisis kegagalan."""
        actions: List[RecoverAction] = []
        evidence: List[str] = []
        affected = failure_analysis.affected_components

        # urutkan komponen: severity turun lalu nama naik (deterministik)
        sev = {f.component: f.severity for f in failure_analysis.failures}
        ordered = sorted(affected, key=lambda c: (-sev.get(c, 0), c))

        seq = 0
        for comp in ordered:
            failure_cls = self._failure_class_of(failure_analysis, comp)
            strategies = _RECOMMENDED.get(failure_cls, (_WAIT,))
            if not strategies or strategies[0] == _NONE:
                continue
            strat = strategies[0]
            seq += 1
            actions.append(
                RecoverAction(
                    action="recover_restore" if strat == _RESTORE else strat,
                    target=comp,
                    strategy=strat,
                    rationale=self._rationale(comp, failure_cls, strat, context),
                    sequence=seq,
                )
            )
            evidence.append("{}:{}".format(comp, failure_cls))

        readiness_gate = self._readiness_gate_of(actions)
        confidence = self._confidence(failure_analysis, actions)
        strategy_id = strategy_id or self._stable_id(context.state_id)
        summary = (
            "Proposed recovery for {} component(s) on state {}; "
            "proposal only, no execution".format(len(affected), context.state_id)
        )
        return RecoveryStrategy(
            strategy_id=strategy_id,
            context=context,
            target_components=tuple(ordered),
            actions=tuple(actions),
            readiness_gate=readiness_gate,
            evidence_basis=tuple(dict.fromkeys(evidence)),
            confidence=confidence,
            summary=summary,
            metadata={"deterministic": True},
        )

    @staticmethod
    def _failure_class_of(fa: FailureAnalysis, comp: str) -> str:
        for f in fa.failures:
            if f.component == comp:
                return f.failure_class
        return "unknown"

    def _rationale(
        self, comp: str, failure_cls: str, strat: str, context: RecoveryContext
    ) -> str:
        # strategi berbasis evidence (failure class) + kondisi readiness
        if strat == _RESTORE:
            return (
                "{} failed as {}; restore recommended because a prerequisite "
                "may satisfice readiness".format(comp, failure_cls)
            )
        if strat == _REPLACE:
            return "{} failed as {}; replace recommended (config/state suspect)".format(
                comp, failure_cls
            )
        if strat == _REBALANCE:
            return "{} failed as {}; rebalance to redistribute load".format(
                comp, failure_cls
            )
        if strat == _RETRY:
            return "{} failed as {}; retry may recover transient failure".format(
                comp, failure_cls
            )
        if strat == _REPLICATE:
            return "{} failed as {}; replicate to restore availability".format(
                comp, failure_cls
            )
        return "{} failed as {}; monitor and wait (no safe strategy yet)".format(
            comp, failure_cls
        )

    def _readiness_gate_of(self, actions: List[RecoverAction]) -> str:
        # gate = strategi paling konservatif yang dibutuhkan
        if not actions:
            return "none"
        return "ready"

    @staticmethod
    def _confidence(fa: FailureAnalysis, actions: List[RecoverAction]) -> int:
        """Confidence proposal berbasis jumlah analisis & coverage."""
        if not actions or fa.failure_count() == 0:
            return 0
        # coverage: berapa proporsi komponen bermasalah punya tindakan
        covered = len(actions)
        total = fa.failure_count()
        pct = int((covered / total) * 100) if total else 0
        return min(95, 40 + int(pct / 2))

    @staticmethod
    def _stable_id(seed: str) -> str:
        import hashlib

        return "rs-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
