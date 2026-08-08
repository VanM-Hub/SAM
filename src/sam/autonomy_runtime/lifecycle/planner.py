# Lifecycle Planner - WP-36
# IP-3.2-004 (AO-3.2-001 / ED-3.2-004)
#
# Menyusun proposal transisi lifecycle & menilai kesiapan (readiness)
# transisi. Hanya PROPOSAL - perubahan status aktual tetap pada runtime yang
# berwenang & governance yang berlaku.
# "Lifecycle Proposal, never Lifecycle Mutation."

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from sam.autonomy_runtime.lifecycle.models import (
    LifecycleState,
    LifecycleTransition,
)
from sam.autonomy_runtime.lifecycle.analyzer import LifecycleAnalyzer


@dataclass(frozen=True)
class LifecycleReadiness:
    """Kesiapan suatu runtime untuk transisi lifecycle (proposal, bukan aksi)."""

    runtime_id: str
    ready: bool
    from_stage: str
    to_stage: str
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "ready": self.ready,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class LifecyclePlan:
    """Rencana lifecycle - proposal transisi + kesiapan (immutable)."""

    plan_id: str
    runtime_id: str
    current_stage: str
    transitions: Tuple[LifecycleTransition, ...] = ()
    readiness: Tuple[LifecycleReadiness, ...] = ()
    health_trend: str = "stable"
    rationale: str = ""
    is_proposal_only: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "runtime_id": self.runtime_id,
            "current_stage": self.current_stage,
            "transitions": [t.as_dict() for t in self.transitions],
            "readiness": [r.as_dict() for r in self.readiness],
            "health_trend": self.health_trend,
            "rationale": self.rationale,
            "is_proposal_only": self.is_proposal_only,
            "metadata": dict(self.metadata),
        }

    def transition_count(self) -> int:
        return len(self.transitions)

    def readiness_count(self) -> int:
        return len(self.readiness)


class LifecyclePlanner:
    """Merencanakan transisi lifecycle berbasis analisis (deterministik)."""

    _ALLOWED_TRANSITIONS = {
        "provisioning": ("starting",),
        "starting": ("running",),
        "running": ("degrading", "draining", "stopping"),
        "degrading": ("running", "draining", "stopping"),
        "draining": ("stopping",),
        "stopping": ("stopped",),
    }

    def __init__(self, analyzer: Optional[LifecycleAnalyzer] = None):
        self._analyzer = analyzer or LifecycleAnalyzer()

    def plan(
        self,
        states: Tuple[LifecycleState, ...],
        target_runtime_id: str = "",
        plan_id: str = "",
    ) -> LifecyclePlan:
        """Susun rencana lifecycle untuk runtime target (atau semua states)."""
        if not states:
            return self._empty_plan("", plan_id)
        target = target_runtime_id or states[0].runtime_id

        # cari state target terbaru (deterministik: urutan tuple pertama)
        target_state = states[0]
        for s in states:
            if s.runtime_id == target:
                target_state = s
                break

        analysis = self._analyzer.analyze(target_state)
        transitions = self._propose_transitions(target_state)
        readiness = self._assess_readiness(target_state, transitions)
        health_trend = self._aggregate_trend(states, target)

        plan_id = plan_id or self._stable_id(target)
        return LifecyclePlan(
            plan_id=plan_id,
            runtime_id=target,
            current_stage=target_state.stage,
            transitions=tuple(transitions),
            readiness=tuple(readiness),
            health_trend=health_trend,
            rationale=analysis.suggestion,
            is_proposal_only=True,
            metadata={"deterministic": True},
        )

    # --- helpers ---

    def _propose_transitions(
        self, state: LifecycleState
    ) -> Tuple[LifecycleTransition, ...]:
        allowed = self._ALLOWED_TRANSITIONS.get(state.stage, ())
        return tuple(
            LifecycleTransition(
                runtime_id=state.runtime_id,
                from_stage=state.stage,
                to_stage=to,
                reason="lifecycle transition proposal",
                is_proposal=True,
            )
            for to in allowed
        )

    def _assess_readiness(
        self,
        state: LifecycleState,
        transitions: Tuple[LifecycleTransition, ...],
    ) -> Tuple[LifecycleReadiness, ...]:
        result = []
        for tr in transitions:
            # transisi ke running membutuhkan readiness healthy
            if tr.to_stage == "running":
                ready = state.readiness == "healthy"
                reason = (
                    "ready to run" if ready
                    else "not ready: runtime not healthy"
                )
            elif tr.to_stage == "stopped":
                ready = state.stage in ("stopping", "draining")
                reason = (
                    "ready to stop" if ready
                    else "not ready: runtime not in stopping/draining"
                )
            else:
                ready = True
                reason = "transition is permitted by lifecycle model"
            result.append(
                LifecycleReadiness(
                    runtime_id=state.runtime_id,
                    ready=ready,
                    from_stage=state.stage,
                    to_stage=tr.to_stage,
                    reason=reason,
                )
            )
        return tuple(result)

    @staticmethod
    def _aggregate_trend(
        states: Tuple[LifecycleState, ...], target: str
    ) -> str:
        trends = [s.health_trend for s in states if s.runtime_id == target]
        if not trends:
            return "stable"
        if "declining" in trends:
            return "declining"
        if "improving" in trends:
            return "improving"
        return "stable"

    @staticmethod
    def _empty_plan(runtime_id: str, plan_id: str) -> LifecyclePlan:
        return LifecyclePlan(
            plan_id=plan_id or "none",
            runtime_id=runtime_id,
            current_stage="unknown",
            rationale="no lifecycle states provided",
            is_proposal_only=True,
        )

    @staticmethod
    def _stable_id(seed: str) -> str:
        import hashlib

        return "lc-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
