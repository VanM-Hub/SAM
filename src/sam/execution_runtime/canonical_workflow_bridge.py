"""Canonical Workflow Bridge - M4 (Canonical Execution Consolidation).

Mengarahkan orchestrator `universal_workflow.WorkflowExecutionEngine` (yang
default-nya menandai step `success=True` TANPA eksekusi nyata) ke jalur
canonical `RealExecutionHarness` (gated, real external execution).

Prinsip:
- Orchestrator workflow BUKAN executor paralel; ia koordinator step.
- Tiap step dieksekusi NYATA lewat `RealExecutionHarness.execute()` (gate
  P2-B: capability, contract, policy, approval, verification, audit).
- Fail-stop: jika satu step gagal (gate / runtime), langkah berikutnya TIDAK
  dijalankan -> tidak ada partial commit.
- Tanpa approval -> step BLOCKED (no external side effect).

Non-destruktif: file `universal_workflow/*` tetap ada sebagai LEGACY; bridge
ini hanya menyuntikkan executor canonical.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

from sam.execution_runtime.real_harness import (
    AuditTrail,
    ExecutionMode,
    ExecutionRequest,
    ExecutionRuntimeResult,
    RealExecutionHarness,
)


@dataclass
class CanonicalStepOutcome:
    """Hasil satu step yang dieksekusi canonical (auditable)."""

    step_id: str
    ok: bool
    operation: str = ""
    target: str = ""
    outcome: Dict[str, Any] = None  # type: ignore[assignment]
    verification: Dict[str, Any] = None  # type: ignore[assignment]
    blocked: bool = False
    error: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "ok": self.ok,
            "operation": self.operation,
            "target": self.target,
            "outcome": self.outcome or {},
            "verification": self.verification or {},
            "blocked": self.blocked,
            "error": self.error,
        }


class CanonicalStepExecutor:
    """Eksekutor step yang membungkus RealExecutionHarness canonical.

    Setiap step = satu ExecutionRequest canonical (operation=tool/<kind>,
    target nyata, approval wajib). Step dijalankan hanya bila semua gate lolos
    (P2-B); hasil + verification + audit direkam.
    """

    def __init__(self, harness: RealExecutionHarness, audit: Optional[AuditTrail] = None) -> None:
        self._harness = harness
        self._audit = audit or harness._audit  # noqa: SLF001 - reuse audit harness

    def execute_step(
        self,
        step_id: str,
        operation: str,
        target: str,
        params: Optional[Dict[str, Any]] = None,
        correlation_id: str = "",
        approval_reason: str = "",
        timeout_seconds: float = 10.0,
        mode: ExecutionMode = ExecutionMode.EXECUTE,
    ) -> CanonicalStepOutcome:
        try:
            req = ExecutionRequest(
                operation=operation,
                target=target,
                params=params or {},
                mode=mode,
                correlation_id=correlation_id or f"wflow-{step_id}",
                timeout_seconds=timeout_seconds,
                approval_reason=approval_reason,
            )
            result: ExecutionRuntimeResult = self._harness.execute(req)
        except Exception as exc:  # noqa: BLE001
            self._audit.record("wflow.step.error", step_id, error=f"{type(exc).__name__}: {exc}")
            return CanonicalStepOutcome(
                step_id=step_id, ok=False, operation=operation, target=target,
                blocked=False, error=f"{type(exc).__name__}: {exc}",
            )
        ok = bool(result.outcome.get("ok")) and not result.outcome.get("blocked")
        oc = CanonicalStepOutcome(
            step_id=step_id,
            ok=ok,
            operation=operation,
            target=target,
            outcome=result.outcome,
            verification=result.verification,
            blocked=bool(result.outcome.get("blocked")) or not ok,
            error="" if ok else str(result.outcome.get("detail", "")),
        )
        self._audit.record(
            "wflow.step.done", step_id,
            ok=ok, operation=operation, target=target, blocked=oc.blocked,
        )
        return oc


def run_gated_workflow(
    steps: List[Dict[str, Any]],
    *,
    harness: Optional[RealExecutionHarness] = None,
    audit: Optional[AuditTrail] = None,
    fail_fast: bool = True,
    default_approval_reason: str = "",
) -> Tuple[bool, List[CanonicalStepOutcome]]:
    """Jalankan rangkaian step canonical dengan fail-stop.

    `steps`: daftar dict berisi step_id, operation, target, params, approval_reason,
    correlation_id, timeout_seconds.

    Returns (all_ok, outcomes). Bila fail_fast dan satu step gagal, berhenti
    (outcomes berisi hasil sampai step gagal) -> no partial commit.
    """
    audit = audit or AuditTrail()
    harness = harness or RealExecutionHarness(audit=audit)
    execr = CanonicalStepExecutor(harness, audit)

    # Daftarkan capability 'tool' bila belum ada (default harness kosong)
    if not harness.capability_exists("tool"):
        from sam.execution_runtime.canonical_tool_contract import (
            build_tool_contract,
            contract_to_registry_dict,
            TOOL_KIND_READ,
            TOOL_KIND_WRITE,
            TOOL_KIND_EXECUTE,
        )
        contract = build_tool_contract(
            tool_id="workflow_tool",
            contract_id="ct-wflow-default",
            supported_kinds=(TOOL_KIND_READ, TOOL_KIND_WRITE, TOOL_KIND_EXECUTE),
            entry_points=("read", "meta", "hash"),
            requires_approval=True,
            requires_governance=True,
        )
        harness.register_capability(
            "tool", contract_to_registry_dict(contract), contract.to_contract_dict(), "ALLOW"
        )

    outcomes: List[CanonicalStepOutcome] = []
    for step in steps:
        oc = execr.execute_step(
            step_id=step.get("step_id", "s"),
            operation=step.get("operation", "tool/read"),
            target=step.get("target", ""),
            params=step.get("params", {}),
            correlation_id=step.get("correlation_id", ""),
            approval_reason=step.get("approval_reason", default_approval_reason),
            timeout_seconds=step.get("timeout_seconds", 10.0),
            mode=ExecutionMode(step.get("mode", "EXECUTE")) if isinstance(step.get("mode", "EXECUTE"), str) else step.get("mode", ExecutionMode.EXECUTE),
        )
        outcomes.append(oc)
        if fail_fast and not oc.ok:
            audit.record("wflow.fail_fast", oc.step_id, reason=oc.error or oc.outcome.get("detail", ""))
            break
    all_ok = all(o.ok for o in outcomes) and len(outcomes) == len(steps)
    return all_ok, outcomes


def build_universal_engine_executor(harness: RealExecutionHarness, audit: Optional[AuditTrail] = None) -> Callable[[str, Dict[str, Any]], "StepExecutionResult"]:
    """Buat callable `executor` untuk WorkflowExecutionEngine.execute(executor=...).

    Universal_workflow engine memanggil `executor(step_id, inputs)` per step.
    Bridge ini menerjemahkan inputs -> ExecutionRequest canonical dan menjalankan
    step lewat harness. Mengembalikan StepExecutionResult pseudo (compatible
    dengan universal_workflow) berbasis hasil nyata.

    Pemakaian:
        from sam.universal_workflow.workflow_execution import WorkflowExecutionEngine
        engine = WorkflowExecutionEngine()
        ctx = engine.execute(request_id, workflow_id, step_ids, inputs, executor=build_universal_engine_executor(harness))

    NOTE: input `inputs` harus berisi kunci operation/target/approval_reason bila
    step ingin dieksekusi nyata; bila kosong, step dianggap BLOCKED (no fake success).
    """
    execr = CanonicalStepExecutor(harness, audit)
    from types import SimpleNamespace

    def _executor(step_id: str, inputs: Dict[str, Any]) -> "StepExecutionResult":
        if not isinstance(inputs, dict) or not inputs.get("target"):
            # Tanpa target nyata -> tidak dieksekusi, bukan sukses palsu
            return SimpleNamespace(
                step_id=step_id, success=False, result={"error": "no real target", "blocked": True}
            )
        oc = execr.execute_step(
            step_id=step_id,
            operation=inputs.get("operation", "tool/read"),
            target=inputs["target"],
            params=inputs.get("params", {}),
            correlation_id=inputs.get("correlation_id", f"wflow-{step_id}"),
            approval_reason=inputs.get("approval_reason", ""),
            timeout_seconds=inputs.get("timeout_seconds", 10.0),
        )
        return SimpleNamespace(
            step_id=step_id, success=oc.ok, result=oc.as_dict()
        )

    return _executor
