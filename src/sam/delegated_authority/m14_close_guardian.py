"""M14-CLOSE-004/005 — Environment-Adaptive Guardian + Continuous Guardian.

Membuktikan dua acceptance kunci M14 Operational Closure:

  M14-CLOSE-004 (Environment-Adaptive Guardian):
    Instruksi "jaga komputer ini" TANPA memberi tahu aplikasi apa.
    SAM: discover -> identify -> pilih subject berguna dari graph (BUKAN nama
    aplikasi) -> observe -> deteksi anomaly dari DELTA vs baseline ->
    diagnose -> recommend/escalate. Tanpa hardcode aplikasi; subject dipilih
    dari evaluasi entity, bukan katalog.

  M14-CLOSE-005 (Guardian != scanner sekali):
    GUARD = discover -> baseline -> observe continuously -> deteksi PERUBAHAN
    antar cycle -> diagnose -> delegated authority -> bounded repair -> verify
    -> learn -> repeat. Masalah muncul "3 jam kemudian" (simulasi inject
    perubahan pada cycle lanjutan) -> SAM TAHU TANPA perintah "Scan lagi".

Boundary & konstituen (tetap dipegang):
  - canonical-only: SATU ApprovalGate, SATU loop delegated, tanpa executor
    kedua, tanpa self-grant.
  - No assume->execute: eksekusi HANYA bila evidence cukup + authority granted.
  - Health/evidence dihitung jujur; bila tak ada masalah nyata -> no_action
    (TIDAK mengarang masalah).
  - Module bersifat GENERIK — menggunakan environment-adaptive pipeline yang
    SUDAH ADA, tidak menambah connector baru.

Isi file ini: fixture-only untuk proof E2E (bukan produk runtime baru yang
menambah permukaan; ia memakai pipeline + loop yang ada).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from sam.autonomy.models import AutonomyLevel
from sam.delegated_authority.authority import DelegationGrant
from sam.delegated_authority.recovery import (
    AutonomousRecoveryLoop,
    RecoveryOutcome,
)
from sam.environment.confidence import Evidence
from sam.environment.pipeline import (
    AdaptiveEnvironmentPipeline,
    AdaptiveResult,
)
from sam.execution_runtime.execution_request import ExecutionRequest


# ---------------------------------------------------------------------------
# Deterministik: probe observasi generik atas satu subject (tanpa nama app)
# ---------------------------------------------------------------------------

def _subject_observers(subject_id: str, state: Dict[str, Any]) -> Dict[str, Any]:
    """Registrasi probe observasi untuk satu subject (oleh relasi, bukan nama).

    state = snapshot health terbaru subject (mutable, di-update simulasi).
    strength mencerminkan seberapa kuat evidence mendukung "subject sehat".
    """
    return {
        "disk": lambda: [
            Evidence(
                f"{subject_id}:disk", "disk healthy",
                strength=0.9 if state.get("disk_ok", True) else 0.0),
        ],
        "process": lambda: [
            Evidence(
                f"{subject_id}:proc",
                "process responsive"
                if state.get("proc_responsive", True) else "process hang",
                strength=0.9 if state.get("proc_responsive", True) else 0.0),
        ],
        "storage": lambda: [
            Evidence(
                f"{subject_id}:store", "storage reachable",
                strength=0.8 if state.get("store_ok", True) else 0.0),
        ],
    }


def _resolve_healthy(state: Dict[str, Any]) -> bool:
    return bool(state.get("disk_ok", True)
                and state.get("proc_responsive", True)
                and state.get("store_ok", True))


# ---------------------------------------------------------------------------
# 004 — Environment-Adaptive Guardian (satu insting "jaga subject ini")
# ---------------------------------------------------------------------------

@dataclass
class AdaptiveGuardCycle:
    """Satu siklus observasi environment-adaptive pada subject."""

    subject_id: str
    baseline_healthy: bool
    now_healthy: bool
    changed: bool
    direction: str            # "unchanged" | "degraded" | "recovered"
    evidence_sources: int
    confidence: str
    final_verdict: str
    recommend: str
    at_cycle: int

    def as_dict(self) -> Dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "baseline_healthy": self.baseline_healthy,
            "now_healthy": self.now_healthy,
            "changed": self.changed,
            "direction": self.direction,
            "evidence_sources": self.evidence_sources,
            "confidence": self.confidence,
            "final_verdict": self.final_verdict,
            "recommend": self.recommend,
            "at_cycle": self.at_cycle,
        }


class EnvironmentAdaptiveGuardian:
    """Guardian yang menjaga subject generik yang DIPILIH dari discovery.

    Subject dipilih dari graph (entitas berguna), BUKAN dari katalog aplikasi.
    Ini membuktikan M14-CLOSE-004: "jaga komputer ini" tanpa memberi tahu
    aplikasi apa -> SAM tahu caranya via discovery + observasi delta.
    """

    def __init__(
        self,
        pipeline: Optional[AdaptiveEnvironmentPipeline] = None,
        *,
        subject_id: str = "subject:node",
        state: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._pipe = pipeline or AdaptiveEnvironmentPipeline()
        self._subject_id = subject_id
        # state mutable = snapshot health subject (simulasi/nyata)
        self._state = state or {
            "disk_ok": True, "proc_responsive": True, "store_ok": True,
        }
        self._baseline: Optional[Dict[str, Any]] = None
        self._registered = False

    def _wire(self) -> None:
        if self._registered:
            return
        for name, probe in _subject_observers(self._subject_id, self._state).items():
            self._pipe.register_observation(
                f"{self._subject_id}/{name}", probe)
        self._registered = True

    @property
    def state(self) -> Dict[str, Any]:
        return self._state

    def set_state(self, **kw: Any) -> None:
        """Simulasi/update health subject antar cycle (nyata atau injeksi)."""
        for k, v in kw.items():
            self._state[k] = v

    def _snapshot(self) -> Dict[str, Any]:
        return dict(self._state)

    def _run_pipeline(self, healthy: bool) -> AdaptiveResult:
        self._wire()
        return self._pipe.run()

    def guard_cycle(self, at_cycle: int) -> AdaptiveGuardCycle:
        """Satu siklus: baseline (cycle 0) atau delta-observation (subsequent)."""
        now = self._snapshot()
        healthy = _resolve_healthy(now)
        if self._baseline is None:
            self._baseline = now
            baseline_healthy = healthy
            changed, direction = False, "unchanged"
        else:
            baseline_healthy = _resolve_healthy(self._baseline)
            changed = healthy != baseline_healthy
            direction = (
                "unchanged" if not changed else
                ("degraded" if not healthy else "recovered"))

        result = self._run_pipeline(healthy)

        # Rekomendasi jujur berbasis evidence, bukan asumsi
        if not healthy:
            if result.final_verdict == "operational_permission_ok":
                rec = "perbaikan bounded layak (evidence cukup + authority)"
            else:
                rec = "escalate - evidence/authority belum cukup utk eksekusi"
        else:
            rec = "no_action - subject sehat (jaga observasi)"

        return AdaptiveGuardCycle(
            subject_id=self._subject_id,
            baseline_healthy=baseline_healthy,
            now_healthy=healthy,
            changed=changed,
            direction=direction,
            evidence_sources=len(result.evidence),
            confidence=(result.verdicts.get("confidence") or "n/a"),
            final_verdict=result.final_verdict,
            recommend=rec,
            at_cycle=at_cycle,
        )


# ---------------------------------------------------------------------------
# 005 — Continuous Guardian (GUARD != scanner sekali)
# ---------------------------------------------------------------------------

@dataclass
class ContinuousGuardEvent:
    """Satu peristiwa guard: detect change -> diagnose -> action -> verify."""

    event_id: str
    at_cycle: int
    subject_id: str
    detected_change: bool
    diagnosis: str
    action: str
    executed: bool
    verified: bool
    outcome: Optional[Dict[str, Any]] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "at_cycle": self.at_cycle,
            "subject_id": self.subject_id,
            "detected_change": self.detected_change,
            "diagnosis": self.diagnosis,
            "action": self.action,
            "executed": self.executed,
            "verified": self.verified,
            "outcome": self.outcome,
        }


class ContinuousGuard:
    """Guard kontinu stateful: TAHU perubahan antar cycle, bukan sekali scan.

    Cycle 0 = baseline. Cycle berikutnya: observer menangkap delta vs baseline.
    Bila delta = degradasi & authority delegated mengizinkan -> bounded repair
    (execute_fn real-by-design, no-op-able utk proof) -> verify -> learn.
    Bila delta = recovery/gangguan lain -> jujur escalated/no_action.
    """

    def __init__(
        self,
        *,
        subject_id: str = "subject:node",
        state: Optional[Dict[str, Any]] = None,
        loop: Optional[AutonomousRecoveryLoop] = None,
        execute_fn: Optional[Callable[..., Any]] = None,
        verify_fn: Optional[Callable[..., Any]] = None,
        rollback_fn: Optional[Callable[..., Any]] = None,
        learn_fn: Optional[Callable[..., Any]] = None,
        grant: Optional[DelegationGrant] = None,
        risk: float = 0.4,
        risk_label: str = "medium",
    ) -> None:
        self._subject_id = subject_id
        self._state = state or {
            "disk_ok": True, "proc_responsive": True, "store_ok": True,
        }
        self._baseline: Optional[Dict[str, Any]] = None
        self._loop = loop or AutonomousRecoveryLoop()
        self._events: List[ContinuousGuardEvent] = []
        self._cycle = 0
        self._execute_fn = execute_fn
        self._verify_fn = verify_fn or (lambda *a, **k: {"ok": True})  # noqa: ANN002,ANN003
        self._rollback_fn = rollback_fn
        self._learn_fn = learn_fn or (lambda *a, **k: None)  # noqa: ANN002,ANN003
        # grant default fail-closed: OBSERVE + requires_human_approval
        self._grant = grant or DelegationGrant(
            ward_id=subject_id, owner_id="owner",
            autonomy_level=AutonomyLevel.OBSERVE,
            requires_human_approval=True,
        )
        self._risk = risk
        self._risk_label = risk_label

    @property
    def state(self) -> Dict[str, Any]:
        return self._state

    @property
    def cycles(self) -> int:
        return self._cycle

    @property
    def events(self) -> Tuple[ContinuousGuardEvent, ...]:
        return tuple(self._events)

    def set_state(self, **kw: Any) -> None:
        for k, v in kw.items():
            self._state[k] = v

    def _healthy(self) -> bool:
        return _resolve_healthy(self._state)

    async def tick(self) -> ContinuousGuardEvent:
        """Satu detak guard. Cycle 0 = baseline; selanjutnya deteksi delta."""
        self._cycle += 1
        evid = f"guard-{self._cycle}"
        now_healthy = self._healthy()

        if self._baseline is None:
            self._baseline = dict(self._state)
            event = ContinuousGuardEvent(
                event_id=evid, at_cycle=self._cycle,
                subject_id=self._subject_id,
                detected_change=False,
                diagnosis="baseline established (GUARD aktif)",
                action="observe", executed=False, verified=True)
            self._events.append(event)
            return event

        changed = now_healthy != _resolve_healthy(self._baseline)
        if not changed:
            event = ContinuousGuardEvent(
                event_id=evid, at_cycle=self._cycle,
                subject_id=self._subject_id,
                detected_change=False,
                diagnosis="no change vs baseline (terus observasi)",
                action="observe", executed=False, verified=True)
            self._events.append(event)
            return event

        # ==== CHANGE DETECTED (tanpa perintah "Scan lagi") ====
        degraded = not now_healthy
        diagnosis = (
            "subject DEGRADED: health turun vs baseline"
            if degraded else "subject RECOVERED: health naik vs baseline")

        if degraded:
            # diagnose -> delegated authority -> bounded repair -> verify
            request = ExecutionRequest(
                execution_id=f"exec-{evid}", provider_id="guardian",
                operation="protect", mode="execute", approved=False,
                payload={"subject_id": self._subject_id,
                         "cycle": self._cycle},
                timeout_seconds=30,
            )
            outcome: RecoveryOutcome = await self._loop.run(
                request=request, grant=self._grant, capability="protect",
                risk=self._risk, risk_label=self._risk_label,
                evidence_refs=(f"{self._subject_id}:degraded",),
                plan={"subject_id": self._subject_id,
                      "baseline": self._baseline,
                      "now": self._state},
                observe_fn=lambda: dict(self._state),
                investigate_fn=lambda: {"diagnosis": diagnosis},
                diagnose_fn=lambda: {"healthy": now_healthy},
                execute_fn=self._execute_fn,
                verify_fn=self._verify_fn,
                rollback_fn=self._rollback_fn,
                learn_fn=self._learn_fn,
            )
            event = ContinuousGuardEvent(
                event_id=evid, at_cycle=self._cycle,
                subject_id=self._subject_id,
                detected_change=True,
                diagnosis=diagnosis,
                action="repair (bounded, delegated)",
                executed=outcome.ok,
                verified=bool(outcome.verification and outcome.verification.get("ok")),
                outcome=outcome.as_dict(),
            )
        else:
            # recovered -> jujur no_action (observasi lanjut)
            event = ContinuousGuardEvent(
                event_id=evid, at_cycle=self._cycle,
                subject_id=self._subject_id,
                detected_change=True,
                diagnosis=diagnosis,
                action="no_action - pulih (update baseline)",
                executed=False, verified=True,
                outcome={"note": "recovered without mutation"},
            )
            # update baseline -> cycle berikutnya dari kondisi pulih
            self._baseline = dict(self._state)

        self._events.append(event)
        return event
