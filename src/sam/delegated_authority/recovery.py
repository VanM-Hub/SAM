"""M14-006 AutonomousRecoveryLoop — loop recovery otonom (orkestrator).

FLOW M14 (dijalankan di sini utk kasus recovery):
    Observe -> Investigate -> Diagnose -> Plan -> Policy -> Risk
    -> Evidence -> Autonomous Authority -> Guardrails -> ApprovalGate
    -> Canonical Execution -> Verification -> Audit -> Learning

Modul ini adalah ORKESTRATOR, BUKAN engine eksekusi. Semua komponen yang
mengeksekusi / menyetujui di-INJEKSIKAN dari luar (composition root):
    - observe_fn / investigate_fn / diagnose_fn: read-only (probe).
    - execute_fn: canonical executor (RealExecutionHarness + ApprovalGate).
    - learn_fn: mencatat pengalaman ke learning store.
Loop TIDAK pernah memanggil connector langsung dan TIDAK membuat executor
kedua.

Ahli otoritas: DelegatedApprovalProvider (M14-002) memutuskan apakah approval
otomatis diizinkan. Bila tidak -> escalate (M14-005) atau berhenti honstly.
Bila verification gagal -> FAILED / ROLLBACK / ESCALATE (TIDAK success=True
tanpa independent verification).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from sam.delegated_authority.authority import (
    AuthorityVerdict,
)
from sam.delegated_authority.escalation import AutomaticEscalation
from sam.delegated_authority.provider import (
    DelegatedApprovalProvider,
)


class RecoveryPhase(str):
    OBSERVE = "observe"
    INVESTIGATE = "investigate"
    DIAGNOSE = "diagnose"
    PLAN = "plan"
    AUTHORITY = "authority"
    EXECUTE = "execute"
    VERIFY = "verify"
    FAILED = "failed"
    ESCALATED = "escalated"
    ROLLED_BACK = "rolled_back"
    COMPLETED = "completed"


@dataclass(frozen=True)
class RecoveryStep:
    """Satu langkah recovery yang ter-audit (immutable)."""

    phase: str
    ok: bool
    detail: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {"phase": self.phase, "ok": self.ok, "detail": self.detail}


@dataclass(frozen=True)
class RecoveryOutcome:
    """Hasil satu siklus recovery (deterministik, auditable)."""

    recovery_id: str
    ward_id: str
    phase: str                        # fase akhir
    ok: bool                          # true HANYA bila independent verification lulus
    steps: tuple = ()
    authority: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None
    verification: Optional[Dict[str, Any]] = None
    reason: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "recovery_id": self.recovery_id,
            "ward_id": self.ward_id,
            "phase": self.phase,
            "ok": self.ok,
            "steps": [s.as_dict() for s in self.steps],
            "authority": self.authority,
            "execution_result": self.execution_result,
            "verification": self.verification,
            "reason": self.reason,
        }


class AutonomousRecoveryLoop:
    """Orkestrator recovery otonom (semua eksekusi via injeksi canonical)."""

    def __init__(
        self,
        provider: Optional[DelegatedApprovalProvider] = None,
        escalation: Optional[AutomaticEscalation] = None,
    ) -> None:
        self._provider = provider or DelegatedApprovalProvider()
        self._escalation = escalation or AutomaticEscalation()
        self._history: List[RecoveryOutcome] = []

    async def run(
        self,
        *,
        request: Any,                 # ExecutionRequest
        grant,                        # DelegationGrant (proyeksi Entrustment)
        capability: Optional[str] = None,   # authority capability (default=request.operation)
        risk: float = 0.0,
        risk_label: str = "low",
        plan: Optional[Dict[str, Any]] = None,
        evidence_refs: tuple = (),
        observe_fn: Optional[Callable[[], Dict[str, Any]]] = None,
        investigate_fn: Optional[Callable[[], Dict[str, Any]]] = None,
        diagnose_fn: Optional[Callable[[], Dict[str, Any]]] = None,
        execute_fn: Optional[Callable[[Any], Dict[str, Any]]] = None,
        verify_fn: Optional[Callable[[Any], Dict[str, Any]]] = None,
        rollback_fn: Optional[Callable[[Any], Dict[str, Any]]] = None,
        learn_fn: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> RecoveryOutcome:
        """Jalankan satu siklus recovery.

        execute_fn/verify_fn WAJIB diinjeksi (canonical); tanpanya recovery
        berhenti honest (FAILED/BLOCKED), bukan sukses palsu.
        """
        recovery_id = f"rec_{uuid4().hex[:12]}"
        ward_id = str(request.payload.get("ward_id", "")) or str(getattr(request, "operation", ""))
        authority_capability = capability or request.operation
        steps: List[RecoveryStep] = []

        # --- Observe --- (read-only)
        obs = self._safe_call(observe_fn)
        steps.append(RecoveryStep(
            RecoveryPhase.OBSERVE, obs is not None,
            {"result": obs} if obs is not None else {"error": "no observe_fn"},
        ))

        # --- Investigate --- (read-only)
        inv = self._safe_call(investigate_fn)
        steps.append(RecoveryStep(
            RecoveryPhase.INVESTIGATE, inv is not None,
            {"result": inv} if inv is not None else {"error": "no investigate_fn"},
        ))

        # --- Diagnose + Plan ---
        diag = self._safe_call(diagnose_fn)
        steps.append(RecoveryStep(
            RecoveryPhase.DIAGNOSE, diag is not None,
            {"result": diag} if diag is not None else {"error": "no diagnose_fn"},
        ))
        steps.append(RecoveryStep(
            RecoveryPhase.PLAN, bool(plan), {"plan": plan or {}},
        ))
        if plan is None:
            plan = {}

        # --- Authority + Approval (delegated) ---
        outcome = await self._provider.approve_for(
            request, grant=grant, risk=risk, risk_label=risk_label,
            evidence_refs=evidence_refs,
            action_context={"ward_id": ward_id, "plan": plan,
                            "capability": authority_capability},
        )
        steps.append(RecoveryStep(
            RecoveryPhase.AUTHORITY, outcome.approved, outcome.as_dict(),
        ))

        # --- Tidak berwenang -> escalate / block / fail ---
        if outcome.verdict in (
            AuthorityVerdict.ESCALATE.value,
            AuthorityVerdict.NO_AUTHORITY.value,
            AuthorityVerdict.BLOCKED.value,
        ):
            esc = await self._escalation.escalate_for(
                ward_id=ward_id,
                capability=authority_capability,
                reason=outcome.reason,
                verdict=AuthorityVerdict(outcome.verdict),
                context={"recovery_id": recovery_id, "authority": outcome.as_dict()},
            )
            phase = RecoveryPhase.ESCALATED if outcome.verdict != AuthorityVerdict.BLOCKED.value \
                else RecoveryPhase.FAILED
            result = RecoveryOutcome(
                recovery_id=recovery_id, ward_id=ward_id, phase=phase,
                ok=False, steps=tuple(steps), authority=outcome.as_dict(),
                reason=f"not auto-approved ({outcome.verdict}): {outcome.reason} "
                       f"-> escalated {esc.id}",
            )
            self._history.append(result)
            return result

        # --- Execute (WAJIB canonical) ---
        if execute_fn is None or verify_fn is None:
            result = RecoveryOutcome(
                recovery_id=recovery_id, ward_id=ward_id,
                phase=RecoveryPhase.FAILED, ok=False,
                steps=tuple(steps), authority=outcome.as_dict(),
                reason="canonical execute_fn/verify_fn not injected - no fake success",
            )
            self._history.append(result)
            return result

        full = self._provider.full_request(request, outcome)
        exec_result = execute_fn(full)
        steps.append(RecoveryStep(
            RecoveryPhase.EXECUTE,
            bool(exec_result and exec_result.get("ok", False)),
            {"result": exec_result},
        ))

        # --- Verification (INDEPENDENT) ---
        verify = verify_fn(full)
        passed = bool(verify and verify.get("ok", False))
        steps.append(RecoveryStep(RecoveryPhase.VERIFY, passed, {"verify": verify}))

        # --- Verdict ---
        if passed:
            # --- Learning (pengalaman sukses) ---
            if learn_fn is not None:
                try:
                    learn_fn({
                        "recovery_id": recovery_id,
                        "ward_id": ward_id,
                        "capability": request.operation,
                        "verdict": "SUCCESS",
                        "evidence": evidence_refs,
                    })
                except Exception:  # noqa: BLE001 - learning tidak menghentikan recovery
                    pass
            result = RecoveryOutcome(
                recovery_id=recovery_id, ward_id=ward_id,
                phase=RecoveryPhase.COMPLETED, ok=True,
                steps=tuple(steps), authority=outcome.as_dict(),
                execution_result=exec_result, verification=verify,
                reason="independent verification passed",
            )
        else:
            # --- Verification gagal: FAILED / ROLLBACK / ESCALATE ---
            outcome_phase = RecoveryPhase.FAILED
            roll = None
            if rollback_fn is not None:
                roll = self._safe_call(rollback_fn, full)
                outcome_phase = RecoveryPhase.ROLLED_BACK
            esc = await self._escalation.escalate_for(
                ward_id=ward_id, capability=request.operation,
                reason="verification failed - escalated for review",
                context={"recovery_id": recovery_id, "verify": verify},
            )
            if outcome_phase != RecoveryPhase.ROLLED_BACK:
                outcome_phase = RecoveryPhase.ESCALATED
            result = RecoveryOutcome(
                recovery_id=recovery_id, ward_id=ward_id,
                phase=outcome_phase, ok=False,
                steps=tuple(steps), authority=outcome.as_dict(),
                execution_result=exec_result, verification=verify,
                reason=f"verification failed: {verify}; rollback={roll}; escalated={esc.id}",
            )
        self._history.append(result)
        return result

    def history(self, limit: int = 100) -> List[RecoveryOutcome]:
        h = list(self._history)
        h.reverse()
        return h[:limit]

    @staticmethod
    def _safe_call(fn, *args) -> Optional[Dict[str, Any]]:
        if fn is None:
            return None
        try:
            r = fn(*args)
            if hasattr(r, "as_dict"):
                return r.as_dict()
            return r
        except Exception as e:  # noqa: BLE001
            return {"error": str(e)}
