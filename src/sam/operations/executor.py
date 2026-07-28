"""
Executor — protocol interface untuk eksekusi ExecutionPlan.

Method:
  prepare()   — persiapan sebelum execute
  execute()   — jalankan actions dalam plan
  verify()    — verifikasi hasil eksekusi
  rollback()  — batalkan eksekusi
  cleanup()   — bersihkan setelah selesai

Belum ada implementasi konkret (ShellExecutor, DockerExecutor, PluginExecutor).
DummyExecutor untuk unit test.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Protocol, Dict, Any
from datetime import datetime
from enum import Enum


class ExecutorState(str, Enum):
    IDLE = "idle"
    PREPARING = "preparing"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    ROLLING_BACK = "rolling_back"
    COMPLETED = "completed"
    FAILED = "failed"
    CLEANED_UP = "cleaned_up"


@dataclass
class ExecutionResult:
    """Hasil eksekusi — lengkap dengan timeline dan evidence."""
    plan_id: str
    state: ExecutorState = ExecutorState.IDLE

    # Timeline
    started_at: str = ""
    completed_at: str = ""
    duration_ms: int = 0

    # Actions
    actions_completed: int = 0
    actions_failed: int = 0
    action_results: List[Dict[str, Any]] = field(default_factory=list)

    # Verification
    verification_passed: bool = False
    verification_results: List[Any] = field(default_factory=list)

    # Rollback
    rollback_executed: bool = False
    rollback_success: bool = False

    # Error
    error_message: str = ""
    failure_reason: str = ""

    def is_success(self) -> bool:
        return self.state == ExecutorState.COMPLETED and self.verification_passed

    def to_text(self) -> str:
        lines = [
            "=== Execution Result: {} ===".format(self.plan_id),
            "State: {}".format(self.state.value),
            "Duration: {}ms".format(self.duration_ms),
            "Actions: {} completed, {} failed".format(self.actions_completed, self.actions_failed),
            "Verification: {}".format("PASSED" if self.verification_passed else "FAILED"),
        ]
        if self.rollback_executed:
            lines.append("Rollback: {}".format("SUCCESS" if self.rollback_success else "FAILED"))
        if self.error_message:
            lines.append("Error: {}".format(self.error_message))
        return "\n".join(lines)


class ExecutorProtocol(Protocol):
    """Protocol for all executors.

    Setiap executor harus implement:
      prepare(plan) -> bool
      execute(plan) -> ExecutionResult
      verify(plan, results) -> bool
      rollback(plan, reason) -> bool
      cleanup(plan) -> bool
    """

    def prepare(self, plan) -> bool:
        """Persiapan — validasi plan, cek resource."""
        ...

    def execute(self, plan) -> ExecutionResult:
        """Eksekusi — jalankan actions dalam plan."""
        ...

    def verify(self, plan, result: ExecutionResult) -> bool:
        """Verifikasi — periksa apakah hasil sesuai expected."""
        ...

    def rollback(self, plan, reason: str = "") -> bool:
        """Rollback — batalkan eksekusi."""
        ...

    def cleanup(self, plan) -> bool:
        """Cleanup — bersihkan resource."""
        ...


class DummyExecutor:
    """Dummy executor untuk testing.

    Tidak melakukan apapun — hanya return hasil simulasi.
    """

    def __init__(self, simulate_success: bool = True):
        self.state = ExecutorState.IDLE
        self._simulate_success = simulate_success

    def prepare(self, plan) -> bool:
        self.state = ExecutorState.PREPARING
        return True

    def execute(self, plan) -> ExecutionResult:
        self.state = ExecutorState.EXECUTING

        result = ExecutionResult(
            plan_id=plan.plan_id,
            state=ExecutorState.COMPLETED if self._simulate_success else ExecutorState.FAILED,
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            duration_ms=150,
            actions_completed=len(plan.actions) if self._simulate_success else 0,
            actions_failed=0 if self._simulate_success else 1,
            action_results=[
                {"action_index": i, "title": getattr(a, 'title', str(a)), "status": "completed" if self._simulate_success else "failed"}
                for i, a in enumerate(plan.actions)
            ],
            verification_passed=self._simulate_success,
        )

        self.state = result.state
        return result

    def verify(self, plan, result: ExecutionResult) -> bool:
        self.state = ExecutorState.VERIFYING
        passed = self._simulate_success
        result.verification_passed = passed
        return passed

    def rollback(self, plan, reason: str = "") -> bool:
        self.state = ExecutorState.ROLLING_BACK
        success = True
        return success

    def cleanup(self, plan) -> bool:
        self.state = ExecutorState.CLEANED_UP
        return True
