# Lifecycle Analyzer - WP-35
# IP-3.2-004 (AO-3.2-001 / ED-3.2-004)
#
# Menganalisis kondisi lifecycle runtime: readiness, fase saat ini, dan
# tren kesehatan (health trend). Hanya analisis - tidak ada transisi nyata.

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from sam.autonomy_runtime.lifecycle.models import LifecycleState


@dataclass(frozen=True)
class LifecycleAnalysis:
    """Hasil analisis lifecycle suatu runtime (immutable, proposal-only)."""

    analysis_id: str
    runtime_id: str
    stage: str
    readiness: str
    health_trend: str
    issues: Tuple[str, ...] = ()
    suggestion: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "runtime_id": self.runtime_id,
            "stage": self.stage,
            "readiness": self.readiness,
            "health_trend": self.health_trend,
            "issues": list(self.issues),
            "suggestion": self.suggestion,
            "metadata": dict(self.metadata),
        }

    def issue_count(self) -> int:
        return len(self.issues)

    def is_healthy(self) -> bool:
        return self.readiness == "healthy" and self.health_trend != "declining"


class LifecycleAnalyzer:
    """Menganalisis lifecycle state -> readiness, tren, isu (deterministik)."""

    def analyze(
        self,
        state: LifecycleState,
        analysis_id: str = "",
    ) -> LifecycleAnalysis:
        readiness = self._readiness(state)
        trend = self._trend(state)
        issues = self._issues(state)
        suggestion = self._suggestion(state, readiness, issues)
        analysis_id = analysis_id or self._stable_id(state.runtime_id)
        return LifecycleAnalysis(
            analysis_id=analysis_id,
            runtime_id=state.runtime_id,
            stage=state.stage,
            readiness=readiness,
            health_trend=trend,
            issues=tuple(issues),
            suggestion=suggestion,
            metadata={"deterministic": True, "proposal_only": True},
        )

    # --- helpers ---

    @staticmethod
    def _readiness(state: LifecycleState) -> str:
        if state.readiness != "unknown":
            return state.readiness
        # infer dari stage bila tidak diberi readiness eksplisit
        if state.stage in ("running", "healthy"):
            return "healthy"
        if state.stage in ("provisioning", "starting", "degrading"):
            return "degraded"
        return "unavailable"

    @staticmethod
    def _trend(state: LifecycleState) -> str:
        if state.health_trend != "unknown":
            return state.health_trend
        if state.stage == "degrading":
            return "declining"
        if state.stage in ("provisioning", "starting"):
            return "improving"
        return "stable"

    @staticmethod
    def _issues(state: LifecycleState) -> Tuple[str, ...]:
        issues = []
        if state.stage == "degrading":
            issues.append("runtime is in degrading stage")
        if state.stage == "stopping":
            issues.append("runtime is stopping")
        if state.stage == "draining":
            issues.append("runtime is draining")
        if state.readiness == "unavailable":
            issues.append("runtime readiness is unavailable")
        return tuple(issues)

    @staticmethod
    def _suggestion(
        state: LifecycleState,
        readiness: str,
        issues: Tuple[str, ...],
    ) -> str:
        if not issues:
            if state.stage == "provisioning":
                return "proposal: proceed to starting stage when ready"
            if state.stage == "running":
                return "proposal: maintain steady-state"
            return "proposal: maintain current lifecycle stage"
        if "declining" in readiness or state.health_trend == "declining":
            return "proposal: consider draining for inspection"
        return "proposal: monitor before any transition"

    @staticmethod
    def _stable_id(seed: str) -> str:
        import hashlib

        return "lca-" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:8]
