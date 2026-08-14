"""M14-009 Real OpenClaw Ward — observe + diagnose + recover OpenClaw.

Target real Van: "Real OpenClaw -> diagnose + recover."

Desain (memakai ulang build-in OpenClaw integration Phase 1, bukan duplikat):
  - observe:  OpenClawHealthCollector.collect()  -> status runtime + komponen.
  - log:      OpenClawLogAnalyzer.analyze()       -> issue dari log.
  - diagnose: gabungkan health + log issues -> temuan terurut.
  - recover:  AutonomousRecoveryLoop (M14-006) dgn execute_fn DIINJEKSIKAN
              (recovery action nyata utk OpenClaw), authority delegated.

Sifat real: health/log collector membaca NYATA dari workspace OpenClaw (file
.openclaw/health.json, logs/*.log). Bila workspace/OpenClaw tak tersedia ->
honest NOT READY / escalate (bukan fake success). E2E real memerlukan runtime
OpenClaw terpasang — ditandai jujur, tidak mengklaim PROVEN tanpa itu.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from sam.autonomy.models import AutonomyLevel
from sam.delegated_authority.authority import DelegationGrant
from sam.delegated_authority.recovery import (
    AutonomousRecoveryLoop, RecoveryOutcome,
)
from sam.openclaw.health import OpenClawHealthCollector
from sam.openclaw.logs import OpenClawLogAnalyzer
from sam.openclaw.models import OpenClawStatus


@dataclass(frozen=True)
class OpenClawDiagnosis:
    """Hasil diagnosis OpenClaw (read-only, auditable)."""

    workspace: str
    runtime_status: str
    component_issues: tuple = ()
    log_issues: tuple = ()
    detections: tuple = ()          # list pesan issue gabungan

    @property
    def healthy(self) -> bool:
        return self.runtime_status == OpenClawStatus.HEALTHY.value \
            and not self.detections

    def as_dict(self) -> Dict[str, Any]:
        return {
            "workspace": self.workspace,
            "runtime_status": self.runtime_status,
            "component_issues": list(self.component_issues),
            "log_issues": list(self.log_issues),
            "detections": list(self.detections),
        }


@dataclass
class OpenClawWardResult:
    """Hasil satu siklus OpenClaw Ward (auditable)."""

    workspace: str
    diagnosis: Optional[OpenClawDiagnosis] = None
    recovered: bool = False
    outcome: Optional[RecoveryOutcome] = None
    reason: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "workspace": self.workspace,
            "diagnosis": self.diagnosis.as_dict() if self.diagnosis else None,
            "recovered": self.recovered,
            "reason": self.reason,
            "outcome": self.outcome.as_dict() if self.outcome else None,
        }


class OpenClawWard:
    """Ward OpenClaw: observe -> diagnose -> recover (delegated authority)."""

    _HAS_REPO = True  # kelas ini memakai openclaw integration yang tersedia

    def __init__(
        self,
        workspace: str,
        collector: Optional[OpenClawHealthCollector] = None,
        analyzer: Optional[OpenClawLogAnalyzer] = None,
        loop: Optional[AutonomousRecoveryLoop] = None,
    ) -> None:
        self.workspace = workspace
        self._collector = collector or OpenClawHealthCollector()
        self._analyzer = analyzer or OpenClawLogAnalyzer(workspace)
        self._loop = loop or AutonomousRecoveryLoop()

    # --- observe ---

    async def diagnose(self) -> OpenClawDiagnosis:
        """Kumpulkan health + log -> diagnosis (read-only)."""
        health = await self._collector.collect(self.workspace)
        runtime_status = health.runtime.value if health.runtime else "unknown"

        component_issues = []
        for comp in health.components:
            if comp.status in (OpenClawStatus.UNHEALTHY, OpenClawStatus.DEGRADED):
                component_issues.append(f"{comp.name}: {comp.message or 'no detail'}")

        log_issues = []
        try:
            log = await self._analyzer.analyze(lines=100)
            log_issues = [
                f"{i['severity']}: {i['message']}" for i in log
                if i.get("severity") in ("ERROR", "CRITICAL", "FATAL", "WARNING")
            ] if all(isinstance(i, dict) for i in log) and log else []
        except Exception:  # noqa: BLE001 - log optional
            log_issues = ["log analysis unavailable"]

        detections = tuple(component_issues + log_issues)
        return OpenClawDiagnosis(
            workspace=self.workspace,
            runtime_status=runtime_status,
            component_issues=tuple(component_issues),
            log_issues=tuple(log_issues),
            detections=detections,
        )

    # --- recover ---

    async def recover(
        self,
        *,
        grant: Optional[DelegationGrant] = None,
        risk: float = 0.4,
        risk_label: str = "medium",
        execute_fn: Optional[Callable] = None,   # recovery action NYATA utk OpenClaw
        verify_fn: Optional[Callable] = None,
        rollback_fn: Optional[Callable] = None,
        learn_fn: Optional[Callable] = None,
    ) -> OpenClawWardResult:
        """Jalankan siklus recovery utk OpenClaw bila ada issue.

        execute_fn/verify_fn diinjeksi (canonical). Tanpa injeksi -> FAILED
        (tidak sukses palsu). Authority delegated (grant); bila tidak cukup ->
        escalate.
        """
        diagnosis = await self.diagnose()

        if diagnosis.healthy:
            return OpenClawWardResult(
                workspace=self.workspace, diagnosis=diagnosis,
                recovered=False, reason="OpenClaw healthy - no recovery needed",
            )

        # grant default fail-closed (human approve bila tidak di-supply)
        grant = grant or DelegationGrant(
            ward_id="openclaw", owner_id="owner",
            autonomy_level=AutonomyLevel.OBSERVE, requires_human_approval=True,
        )

        from sam.execution_runtime.execution_request import ExecutionRequest
        request = ExecutionRequest(
            execution_id=f"exec-ocl-{self.workspace.replace(chr(92),'_').replace('/','_')}",
            provider_id="openclaw", operation="recover", mode="execute",
            approved=False, payload={"ward_id": "openclaw", "workspace": self.workspace},
            timeout_seconds=30,
        )

        outcome = await self._loop.run(
            request=request, grant=grant, capability="protect",
            risk=risk, risk_label=risk_label,
            evidence_refs=(f"runtime:{diagnosis.runtime_status}",),
            plan={"diagnosis": diagnosis.as_dict()},
            observe_fn=lambda: {"runtime_status": diagnosis.runtime_status,
                                "component_issues": list(diagnosis.component_issues)},
            investigate_fn=lambda: {"log_issues": list(diagnosis.log_issues)},
            diagnose_fn=lambda: {"detections": list(diagnosis.detections)},
            execute_fn=execute_fn,
            verify_fn=verify_fn,
            rollback_fn=rollback_fn,
            learn_fn=learn_fn,
        )

        return OpenClawWardResult(
            workspace=self.workspace, diagnosis=diagnosis,
            recovered=outcome.ok, outcome=outcome,
            reason=outcome.reason,
        )

    def history(self, limit: int = 100):
        return self._loop.history(limit)
