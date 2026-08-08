# Lifecycle State Model - WP-34
# IP-3.2-004 (AO-3.2-001 / ED-3.2-004)
#
# Model siklus hidup runtime - fase yang mungkin & transisi yang diusulkan.
# Prinsip: "Lifecycle proposal, never lifecycle mutation."
# Lifecycle Engine BOLEH menyatakan bahwa suatu runtime "siap" atau
# "disarankan berpindah fase". Perubahan status aktual tetap berada pada
# runtime yang berwenang & governance yang berlaku.
# Per ADR-023: frozen dataclasses (immutable DTO).

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


class LifecycleStage:
    """Fase siklus hidup runtime (konstanta string)."""

    PROVISIONING = "provisioning"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADING = "degrading"
    STOPPING = "stopping"
    STOPPED = "stopped"
    DRAINING = "draining"
    HEALTHY = "healthy"

    # urutan garis besar fase (untuk analisis tren, bukan eksekusi)
    ORDER = (
        PROVISIONING, STARTING, RUNNING, DEGRADING,
        DRAINING, STOPPING, STOPPED,
    )


@dataclass(frozen=True)
class LifecycleState:
    """Kondisi lifecycle suatu runtime pada satu titik waktu (immutable)."""

    runtime_id: str
    stage: str  # salah satu LifecycleStage
    observed_at: str
    readiness: str = "unknown"  # healthy | degraded | unavailable | unknown
    health_trend: str = "stable"  # improving | stable | declining
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "stage": self.stage,
            "observed_at": self.observed_at,
            "readiness": self.readiness,
            "health_trend": self.health_trend,
            "metadata": dict(self.metadata),
        }

    def is_running(self) -> bool:
        return self.stage == LifecycleStage.RUNNING


@dataclass(frozen=True)
class LifecycleTransition:
    """Transisi lifecycle yang DIUSULKAN (bukan aksi nyata)."""

    runtime_id: str
    from_stage: str
    to_stage: str
    reason: str = ""
    is_proposal: bool = True

    def as_dict(self) -> Dict[str, Any]:
        return {
            "runtime_id": self.runtime_id,
            "from_stage": self.from_stage,
            "to_stage": self.to_stage,
            "reason": self.reason,
            "is_proposal": self.is_proposal,
        }


@dataclass(frozen=True)
class LifecycleMetadata:
    """Metadata analisis lifecycle - asal usul, basis bukti, determinisme."""

    lifecycle_id: str
    runtime_id: str
    basis: str
    engine: str = "runtime_lifecycle"
    deterministic: bool = True
    generated_by: str = "lifecycle_analysis"
    phase: str = "transitory"  # transitory (proposal only) - bukan operational
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "lifecycle_id": self.lifecycle_id,
            "runtime_id": self.runtime_id,
            "basis": self.basis,
            "engine": self.engine,
            "deterministic": self.deterministic,
            "generated_by": self.generated_by,
            "phase": self.phase,
            "metadata": dict(self.metadata),
        }
