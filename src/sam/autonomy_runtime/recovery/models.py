# Recovery State Model - WP-21
# IP-3.2-003 (AO-3.2-001 / ED-3.2-003)
#
# Immutable recovery context & recovery metadata.
# Prinsip IP-3.2-003: "Recover by strategy, never by authority."
# Runtime boleh memahami kegagalan & menyusun strategi recovery, TIDAK boleh
# melakukan recovery konstitusional secara sepihak. Seluruh output = proposal.
# Per ADR-023: frozen dataclasses (immutable DTO).

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class RecoveryContext:
    """Konteks strategi recovery - snapshot kegagalan & kondisi yang diamati.

    Mencakup identitas state runtime, kondisi kesehatan, readiness, komponen
    yang terpengaruh (dari PlanningContext/observasi), dan dependency. Bersifat
    immutable - dibuat dari hasil observasi + diagnostics + planning, dan tidak
    pernah dimodifikasi oleh recovery.
    """

    state_id: str
    overall_health: str = "unknown"  # healthy | degraded | unhealthy | unknown
    readiness_level: str = "unknown"
    failed_components: Tuple[str, ...] = ()
    degraded_components: Tuple[str, ...] = ()
    healthy_components: Tuple[str, ...] = ()
    dependency_edges: Tuple[Tuple[str, str], ...] = ()
    detected_failures: Tuple[Tuple[Any, ...], ...] = ()  # tuple of (component, verdict, detail)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "state_id": self.state_id,
            "overall_health": self.overall_health,
            "readiness_level": self.readiness_level,
            "failed_components": list(self.failed_components),
            "degraded_components": list(self.degraded_components),
            "healthy_components": list(self.healthy_components),
            "dependency_edges": [list(e) for e in self.dependency_edges],
            "detected_failures": [list(f) for f in self.detected_failures],
            "metadata": dict(self.metadata),
        }

    def failed_components_count(self) -> int:
        return len(self.failed_components)

    def all_affected_components(self) -> Tuple[str, ...]:
        """Komponen gagal + degraded (yang membutuhkan perhatian recovery)."""
        return tuple(sorted(set(self.failed_components) | set(self.degraded_components)))


@dataclass(frozen=True)
class RecoveryMetadata:
    """Metadata strategi recovery - asal usul, basis bukti, determinisme."""

    recovery_id: str
    created_at: str
    basis: str  # deskripsi kegagalan yang diamati
    engine: str = "runtime_recovery"
    deterministic: bool = True
    evidence_refs: Tuple[str, ...] = ()
    generated_by: str = "recovery_analysis"
    phase: str = "strategic"  # strategic (proposal only) - bukan operational
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "recovery_id": self.recovery_id,
            "created_at": self.created_at,
            "basis": self.basis,
            "engine": self.engine,
            "deterministic": self.deterministic,
            "evidence_refs": list(self.evidence_refs),
            "generated_by": self.generated_by,
            "phase": self.phase,
            "metadata": dict(self.metadata),
        }
