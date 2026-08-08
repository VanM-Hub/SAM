# Runtime Observation API - WP-08
# IP-3.2-001 (AO-3.2-001 / ED-3.2-001)
#
# API observasi runtime: ekspos hasil observasi (state, snapshots, health,
# diagnostics, readiness) secara read-only. Tidak ada endpoint yang memicu
# aksi/recovery/restart/orchestration. Hanya query.

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sam.autonomy_runtime.observation.engine import ObservationEngine
from sam.autonomy_runtime.observation.models import RuntimeState, RuntimeSnapshot
from sam.autonomy_runtime.diagnostics.engine import DiagnosticsEngine, RuntimeDiagnostics
from sam.autonomy_runtime.diagnostics.health import HealthAnalyzer, RuntimeHealthReport
from sam.autonomy_runtime.diagnostics.failure import FailureClassifier, FailureClassification
from sam.autonomy_runtime.readiness.analyzer import ReadinessAnalyzer, ReadinessAssessment


@dataclass(frozen=True)
class ObservationSummary:
    """Ringkasan observasi runtime dalam satu jawaban (read-only)."""

    state: RuntimeState
    snapshot: RuntimeSnapshot
    health: RuntimeHealthReport
    diagnostics: RuntimeDiagnostics
    classification: FailureClassification
    readiness: ReadinessAssessment

    def as_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.as_dict(),
            "snapshot": self.snapshot.as_dict(),
            "health": self.health.as_dict(),
            "diagnostics": self.diagnostics.as_dict(),
            "classification": self.classification.as_dict(),
            "readiness": self.readiness.as_dict(),
        }


class RuntimeObservationAPI:
    """Fasad read-only untuk observasi runtime (MISSION-3.2 / IP-3.2-001)."""

    def __init__(
        self,
        engine: ObservationEngine,
        diagnostics: Optional[DiagnosticsEngine] = None,
        health: Optional[HealthAnalyzer] = None,
        failure: Optional[FailureClassifier] = None,
        readiness: Optional[ReadinessAnalyzer] = None,
    ):
        self._engine = engine
        self._diagnostics = diagnostics or DiagnosticsEngine()
        self._health = health or HealthAnalyzer()
        self._failure = failure or FailureClassifier()
        self._readiness = readiness or ReadinessAnalyzer()

    # --- Endpoint query (semua read-only) ---

    def get_state(self) -> RuntimeState:
        return self._engine.observe()

    def get_snapshot(self) -> RuntimeSnapshot:
        return self._engine.snapshot()

    def get_health(self) -> RuntimeHealthReport:
        return self._health.analyze(self._engine.observe())

    def get_diagnostics(self) -> RuntimeDiagnostics:
        return self._diagnostics.diagnose(self._engine.observe())

    def get_classification(self) -> FailureClassification:
        return self._failure.classify(self._engine.observe())

    def get_readiness(self) -> ReadinessAssessment:
        return self._readiness.assess(self._engine.observe())

    def get_summary(self) -> ObservationSummary:
        state = self._engine.observe()
        return ObservationSummary(
            state=state,
            snapshot=self._engine.snapshot(state),
            health=self._health.analyze(state),
            diagnostics=self._diagnostics.diagnose(state),
            classification=self._failure.classify(state),
            readiness=self._readiness.assess(state),
        )

    def list_components(self) -> List[str]:
        return self._engine.component_names()

    def component_names(self) -> List[str]:
        return self.list_components()
