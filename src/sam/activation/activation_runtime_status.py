"""Activation Runtime Status — status runtime keseluruhan."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sam.activation.activation_runtime import RuntimeStatus
from sam.activation.activation_snapshot import ActivationSnapshotState
from sam.activation.activation_health import ActivationHealthReport


@dataclass(frozen=True)
class ActivationRuntimeStatus:
    overall_status: str = "idle"
    phase: str = "idle"
    package_count: int = 0
    ready: bool = False
    health: float = 0.0
    issues: List[str] = field(default_factory=list)


class ActivationRuntimeStatusBuilder:
    """Membangun status runtime keseluruhan."""

    def build(self, engine_status: RuntimeStatus, health: ActivationHealthReport,
              phase: str) -> ActivationRuntimeStatus:
        overall = "ready" if engine_status.status == "idle" and health.healthy and engine_status.total_packages > 0 else engine_status.status
        return ActivationRuntimeStatus(
            overall_status=overall,
            phase=phase,
            package_count=engine_status.total_packages,
            ready=overall == "ready",
            health=health.score,
            issues=health.issues,
        )
