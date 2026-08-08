# Runtime Failure Classification - WP-06
# IP-3.2-001 (AO-3.2-001 / ED-3.2-001)
#
# Mengklasifikasikan penyebab kegagalan komponen ke taksonomi deterministik.
# Murni analisis (read-only): tidak memperbaiki, tidak men-trigger recovery,
# tidak mengubah state.

from dataclasses import dataclass
from typing import Dict, List, Optional

from sam.autonomy_runtime.observation.models import ComponentState, RuntimeState
from sam.autonomy_runtime.observation.dependency import DependencyGraph
from sam.autonomy_runtime.diagnostics.health import RuntimeHealthReport


class FailureClass:
    """Taksonomi penyebab kegagalan (konstanta aja)."""

    DEPENDENCY = "dependency_failure"
    RESOURCE = "resource_exhaustion"
    CONFIG = "configuration_error"
    CONNECTIVITY = "connectivity_failure"
    UNKNOWN = "unknown"
    NONE = "none"


# Kata kunci untuk menebak kelas penyebab dari detail/status observasi.
_PATTERNS = {
    FailureClass.RESOURCE: ("memory", "cpu", "disk", "resource", "quota", "limit", "out of"),
    FailureClass.CONNECTIVITY: ("connect", "timeout", "network", "socket", "refused", "unreachable"),
    FailureClass.CONFIG: ("config", "misconfig", "invalid setting", "not found", "unknown option"),
    FailureClass.DEPENDENCY: ("dependency", "upstream", "prerequisite", "not ready", "unavailable"),
}


@dataclass(frozen=True)
class FailureClassification:
    state_id: str
    observed_at: str
    classifications: dict = None  # Dict[str, str]: component -> FailureClass

    def __post_init__(self):
        if self.classifications is None:
            object.__setattr__(self, "classifications", {})

    def class_of(self, component: str) -> str:
        return self.classifications.get(component, FailureClass.NONE)

    def failed_components(self) -> List[str]:
        return sorted(
            c for c, cls in self.classifications.items()
            if cls != FailureClass.NONE
        )

    def as_dict(self) -> Dict[str, object]:
        return {
            "state_id": self.state_id,
            "observed_at": self.observed_at,
            "classifications": dict(self.classifications or {}),
        }


class FailureClassifier:
    """Mengklasifikasikan kegagalan berdasarkan observasi (deterministik)."""

    def __init__(self, dependency_graph: Optional[DependencyGraph] = None):
        self._graph = dependency_graph or DependencyGraph()

    def classify(self, state: RuntimeState) -> FailureClassification:
        classes: Dict[str, str] = {}
        by_name = {c.name: c for c in state.components}
        nodes = self._graph.nodes()
        for comp in state.components:
            if comp.status == "ok":
                classes[comp.name] = FailureClass.NONE
                continue
            classes[comp.name] = self._classify_component(comp, by_name, nodes)
        return FailureClassification(
            state_id=state.state_id,
            observed_at=state.observed_at,
            classifications=classes,
        )

    def _classify_component(
        self,
        comp: ComponentState,
        by_name: Dict[str, ComponentState],
        nodes: List[str],
    ) -> str:
        # 1) dependency tidak siap -> dependency_failure
        deps = self._graph.dependencies_of(comp.name) or comp.dependencies
        for dep in deps:
            dep_comp = by_name.get(dep)
            if dep_comp is None:
                return FailureClass.DEPENDENCY
            if not dep_comp.ready or dep_comp.status in ("error", "degraded"):
                return FailureClass.DEPENDENCY
        # 2) cocokkan detail/status dengan pola kata kunci
        haystack = "{} {}".format(comp.status, comp.detail).lower()
        for cls, keywords in _PATTERNS.items():
            for kw in keywords:
                if kw in haystack:
                    return cls
        return FailureClass.UNKNOWN
