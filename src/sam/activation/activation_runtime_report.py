"""Activation Runtime Report — laporan akhir runtime."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sam.activation.activation_runtime import RuntimeStatus
from sam.activation.activation_metrics import ActivationMetrics
from sam.activation.activation_snapshot import ActivationSnapshotState
from sam.activation.activation_health import ActivationHealthReport


@dataclass(frozen=True)
class RuntimeReport:
    report_id: str = ""
    status: str = "idle"
    total_packages: int = 0
    ready_for_execution: bool = False
    health_score: float = 0.0
    phases_completed: List[str] = field(default_factory=list)
    summary: str = ""


class RuntimeReportBuilder:
    """Membangun laporan akhir runtime."""

    def build(self, report_id: str, status: RuntimeStatus,
              metrics: ActivationMetrics,
              health: ActivationHealthReport,
              phases: List[str]) -> RuntimeReport:
        ready = status.pipeline_running == False and metrics.total_packages > 0 and health.healthy
        return RuntimeReport(
            report_id=report_id,
            status=status.status,
            total_packages=metrics.total_packages,
            ready_for_execution=ready,
            health_score=health.score,
            phases_completed=phases,
            summary=f"Status={status.status}, packages={metrics.total_packages}, ready={ready}, health={health.score:.2f}",
        )
