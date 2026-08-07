"""Simulation Integration (Program G - Execution Evolution, 2026-08-07).

Exec: Zara, Lead Implementation Engineer. Arah: Architect (2026-08-07).

Menghubungkan Simulation ke pipeline eksekusi sesuai posisi konseptual:
    Mission -> Workflow -> Policy -> Simulation -> Approval -> Execution
        -> Verification -> Audit

Wiring ini:
  - Menjalankan SimulationEngine untuk menghasilkan SimulationEvidence.
  - Menempelkan evidence sebagai INPUT OPSIONAL ke pipeline (tidak mengubah
    kontrak ApprovalGate / ADR-001; evidence memperkaya decision + audit).
  - Menjamin network tetap 0 untuk mode simulation/preview (no external call).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .execution_request import ExecutionRequest
from .simulation_evidence import SimulationEvidence
from .simulation_engine import SimulationEngine, SimulationReport


@dataclass(frozen=True)
class SimulatedExecutionReport:
    """Hasil wiring Simulation -> Approval -> Pipeline (immutable)."""

    simulation: SimulationReport
    approval_applied: bool = False
    external_calls: int = 0
    notes: tuple = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "simulation": self.simulation.as_dict(),
            "approval_applied": self.approval_applied,
            "external_calls": self.external_calls,
            "notes": list(self.notes),
        }


class SimulationIntegration:
    """Titik masuk terintegrasi Simulation di Execution Runtime."""

    def __init__(self, engine: SimulationEngine | None = None) -> None:
        self._engine = engine or SimulationEngine()

    @property
    def engine(self) -> SimulationEngine:
        return self._engine

    def preview(self, request: ExecutionRequest) -> SimulatedExecutionReport:
        """Mode PREVIEW: jalankan simulasi, jaringan = 0, tanpa approval."""
        req = request if request.mode == "simulation" else _with_mode(request, "simulation")
        report = self._engine.run(req)
        return SimulatedExecutionReport(
            simulation=report,
            approval_applied=False,
            external_calls=0,
            notes=("mode=preview: no approval applied, no external call",),
        )

    def dry_run(self, request: ExecutionRequest) -> SimulatedExecutionReport:
        """Mode DRY RUN: pipeline berjalan penuh TAPI external_calls tetap 0."""
        report = self._engine.run(request)
        return SimulatedExecutionReport(
            simulation=report,
            approval_applied=request.approved,
            external_calls=0,
            notes=("mode=dry_run: pipeline active, external_calls=0",),
        )

    def evidence_for_approval(self, request: ExecutionRequest) -> SimulationEvidence:
        """Sediakan evidence (opsional) untuk memperkaya keputusan approval."""
        return self._engine.simulate(request)


def _with_mode(request: ExecutionRequest, mode: str) -> ExecutionRequest:
    """Salin request dengan mode tertentu (immutable request -> salin baru)."""
    return ExecutionRequest(
        execution_id=request.execution_id,
        provider_id=request.provider_id,
        operation=request.operation,
        payload=dict(request.payload),
        mode=mode,
        timeout_seconds=request.timeout_seconds,
        max_retries=request.max_retries,
        cancellation_token=request.cancellation_token,
        approved=request.approved,
        approver=request.approver,
        deterministic=request.deterministic,
        synchronous=request.synchronous,
    )
