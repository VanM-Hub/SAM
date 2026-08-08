# Runtime Diagnostics Engine - WP-05
# IP-3.2-001 (AO-3.2-001 / ED-3.2-001)
#
# Mesin diagnostik: menyatukan state + health + dependency menjadi temuan
# terstruktur dan rekomendasi OBSERVASIONAL (bukan aksi). Tidak pernah
# men-trigger recovery/restart/orchestration.

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sam.autonomy_runtime.observation.models import RuntimeState
from sam.autonomy_runtime.observation.dependency import DependencyGraph
from sam.autonomy_runtime.diagnostics.health import (
    HealthAnalyzer,
    RuntimeHealthReport,
)


@dataclass(frozen=True)
class DiagnosticFinding:
    component: str
    severity: str  # "critical" | "warning" | "info"
    message: str

    def as_dict(self) -> Dict[str, str]:
        return {
            "component": self.component,
            "severity": self.severity,
            "message": self.message,
        }


@dataclass(frozen=True)
class ObservationalRecommendation:
    component: str
    kind: str  # observasi lanjutan yang disarankan (bukan aksi)
    reason: str

    def as_dict(self) -> Dict[str, str]:
        return {
            "component": self.component,
            "kind": self.kind,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class RuntimeDiagnostics:
    state_id: str
    observed_at: str
    overall: str
    findings: tuple = ()  # tuple[DiagnosticFinding]
    recommendations: tuple = ()  # tuple[ObservationalRecommendation]
    root_candidates: tuple = ()  # tuple[str] kemungkinan akar penyebab
    bottleneck_candidates: tuple = ()  # tuple[str]

    def as_dict(self) -> Dict[str, object]:
        return {
            "state_id": self.state_id,
            "observed_at": self.observed_at,
            "overall": self.overall,
            "findings": [f.as_dict() for f in self.findings],
            "recommendations": [r.as_dict() for r in self.recommendations],
            "root_candidates": list(self.root_candidates),
            "bottleneck_candidates": list(self.bottleneck_candidates),
        }


class DiagnosticsEngine:
    """Mensintesis state + health + dependency menjadi diagnostics."""

    def __init__(
        self,
        health_analyzer: Optional[HealthAnalyzer] = None,
        dependency_graph: Optional[DependencyGraph] = None,
    ):
        self._health = health_analyzer or HealthAnalyzer()
        self._graph = dependency_graph or DependencyGraph()

    def diagnose(self, state: RuntimeState) -> RuntimeDiagnostics:
        health = self._health.analyze(state)
        findings: List[DiagnosticFinding] = []
        recommendations: List[ObservationalRecommendation] = []

        # finding dari health report
        by_name = {c.name: c for c in state.components}
        for comp in health.components:
            if comp.status == "unhealthy":
                findings.append(
                    DiagnosticFinding(
                        component=comp.component,
                        severity="critical",
                        message="component is unhealthy",
                    )
                )
            elif comp.status == "degraded":
                findings.append(
                    DiagnosticFinding(
                        component=comp.component,
                        severity="warning",
                        message="component is degraded",
                    )
                )
            if not comp.ready and by_name.get(comp.component) is not None:
                rec_kind = "inspect_dependency"
                rec_reason = "{} not ready; check upstream prerequisite".format(
                    comp.component
                )
                recommendations.append(
                    ObservationalRecommendation(
                        component=comp.component,
                        kind=rec_kind,
                        reason=rec_reason,
                    )
                )

        # root candidates dari dependency (komponen error akar)
        root_candidates = tuple(self._graph.root_failures(state))

        # bottleneck candidates: komponen degraded dengan banyak dependents
        bottleneck = self._bottleneck_candidates(state, health.overall)

        return RuntimeDiagnostics(
            state_id=state.state_id,
            observed_at=state.observed_at,
            overall=health.overall,
            findings=tuple(findings),
            recommendations=tuple(recommendations),
            root_candidates=root_candidates,
            bottleneck_candidates=bottleneck,
        )

    def _bottleneck_candidates(
        self, state: RuntimeState, overall: str
    ) -> tuple:
        if overall == "healthy" or not self._graph.nodes():
            return ()
        # komponen yang dimiliki banyak dependents = rawan bottleneck
        scores: Dict[str, int] = {}
        by_name = {c.name: c for c in state.components}
        for node in self._graph.nodes():
            dependents = self._graph.dependents_of(node)
            comp = by_name.get(node)
            if comp is None:
                continue
            # bobot: banyak dependents + status tidak healthy
            w = len(dependents)
            if comp.status in ("error", "degraded"):
                w += 2
            if w > 0:
                scores[node] = w
        ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        return tuple(k for k, _ in ordered[:3])
