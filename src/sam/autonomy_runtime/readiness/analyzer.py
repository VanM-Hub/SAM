# Runtime Readiness Analyzer - WP-07
# IP-3.2-001 (AO-3.2-001 / ED-3.2-001)
#
# Menilai kesiapan (readiness) runtime untuk beroperasi. Murni penilaian
# (read-only): TIDAK men-trigger start/stop, TIDAK mengubah lifecycle,
# TIDAK menjalankan apapun.

from dataclasses import dataclass
from typing import Dict, List, Optional

from sam.autonomy_runtime.observation.models import RuntimeState
from sam.autonomy_runtime.observation.dependency import DependencyGraph
from sam.autonomy_runtime.diagnostics.health import HealthAnalyzer


@dataclass(frozen=True)
class ReadinessAssessment:
    state_id: str
    observed_at: str
    ready: bool
    level: str  # "ready" | "degraded" | "not_ready" | "unknown"
    blocking: tuple = ()  # tuple[str] komponen/isu yang memblokir

    def as_dict(self) -> Dict[str, object]:
        return {
            "state_id": self.state_id,
            "observed_at": self.observed_at,
            "ready": self.ready,
            "level": self.level,
            "blocking": list(self.blocking),
        }


class ReadinessAnalyzer:
    """Menilai kesiapan runtime (deterministik, read-only)."""

    def __init__(
        self,
        health_analyzer: Optional[HealthAnalyzer] = None,
        dependency_graph: Optional[DependencyGraph] = None,
        required_status: Optional[List[str]] = None,
    ):
        self._health = health_analyzer or HealthAnalyzer()
        self._graph = dependency_graph or DependencyGraph()
        # komponen yang WAJIB ready agar runtime dinyatakan siap.
        # Default minimal: 'kernel' (fondasi). Komponen lain dinilai dari yang
        # benarbener teramati di state, bukan komponen fiktif yang tidak ada.
        self._required = required_status or ["kernel"]

    def assess(self, state: RuntimeState) -> ReadinessAssessment:
        health = self._health.analyze(state)
        blocking: List[str] = []

        # 1) semua komponen wajib harus ada & siap
        by_name = {c.name: c for c in state.components}
        for req in self._required:
            comp = by_name.get(req)
            if comp is None:
                blocking.append("missing required component: {}".format(req))
            elif not comp.ready:
                blocking.append("required component not ready: {}".format(req))
            elif comp.status in ("error", "degraded"):
                blocking.append("required component unhealthy: {}".format(req))

        # 2) komponen error sebagai akar (root failures) = blocker
        for root in self._graph.root_failures(state):
            blocking.append("root failure: {}".format(root))

        # 3) unresolved dependency pada komponen wajib
        for req in self._required:
            if req in by_name and self._graph.nodes():
                unresolved = self._graph.unresolved_dependencies(state, req)
                for u in unresolved:
                    blocking.append("unresolved dependency {} -> {}".format(req, u))

        # tentukan level
        if blocking:
            level = "not_ready"
            ready = False
        elif health.overall == "degraded":
            level = "degraded"
            ready = False
        elif health.overall == "healthy":
            level = "ready"
            ready = True
        else:
            level = "unknown"
            ready = False

        return ReadinessAssessment(
            state_id=state.state_id,
            observed_at=state.observed_at,
            ready=ready,
            level=level,
            blocking=tuple(dict.fromkeys(blocking)),
        )
