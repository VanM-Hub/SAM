"""Environment-adaptive: adaptor ke eksekusi canonical (M14 governance).

Menghubungkan hasil diagnosis environment-adaptive ke AutonomousRecoveryLoop
(canonical), sehingga remediasi TETAP melewati ApprovalGate + RealExecutionHarness.
SAM TIDAK execute connector langsung; loop canonical yang menjalankan.

Ini membuktikan prinsip: "bila diizinkan, diperbaiki" - tapi izin datang dari
delegated authority (grant owner) + ApprovalGate, bukan dari SAM.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

from sam.delegated_authority.authority import DelegationGrant
from sam.delegated_authority.recovery import (
    AutonomousRecoveryLoop,
    RecoveryOutcome,
)


@dataclass
class CanonicalRun:
    """Hasil koneksi pipeline adaptive -> recovery canonical."""

    executed: bool                # apakah loop canonical berhasil menjalankan
    outcome: Optional[RecoveryOutcome] = None
    reason: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "executed": self.executed,
            "outcome": self.outcome.as_dict() if self.outcome else None,
            "reason": self.reason,
        }


class AdaptiveCanonicalBridge:
    """Jembatan pipeline-adaptive ke recovery loop canonical.

    Grant diberikan OWNER (DelegationGrant). Pipeline adaptive hanya
    MENYIAPKAN rencana remediation; bridge ini yang memanggil loop canonical
    dengan execute_fn/verify_fn yang diinjeksi (dari RealExecutionHarness).
    Bila loop menolak/eskalasi -> executed=False, jujur.
    """

    def __init__(
        self,
        loop: Optional[AutonomousRecoveryLoop] = None,
    ) -> None:
        self._loop = loop or AutonomousRecoveryLoop()

    async def run_for(
        self,
        request: Any,               # ExecutionRequest canonical
        grant: DelegationGrant,     # dari owner
        capability: str,            # mis. "repair" / "protect"
        risk: float,
        risk_label: str,
        plan: Dict[str, Any],
        evidence_refs: tuple,
        execute_fn: Callable[[Any], Dict[str, Any]],
        verify_fn: Callable[[Any], Dict[str, Any]],
        learn_fn: Optional[Callable[[Dict[str, Any]], None]] = None,
        observe_fn: Optional[Callable[[], Dict[str, Any]]] = None,
        investigate_fn: Optional[Callable[[], Dict[str, Any]]] = None,
        diagnose_fn: Optional[Callable[[], Dict[str, Any]]] = None,
        rollback_fn: Optional[Callable[[Any], Dict[str, Any]]] = None,
    ) -> CanonicalRun:
        outcome = await self._loop.run(
            request=request,
            grant=grant,
            capability=capability,
            risk=risk,
            risk_label=risk_label,
            plan=plan,
            evidence_refs=evidence_refs,
            observe_fn=observe_fn,
            investigate_fn=investigate_fn,
            diagnose_fn=diagnose_fn,
            execute_fn=execute_fn,
            verify_fn=verify_fn,
            rollback_fn=rollback_fn,
            learn_fn=learn_fn,
        )
        return CanonicalRun(
            executed=outcome.ok,
            outcome=outcome,
            reason=outcome.reason,
        )
