"""Production Execution - IP-4.1-003 WP-21..27.

Production Execution.
Menjadikan jalur execution siap digunakan pada operasi nyata: multi-provider,
reliability, retry policy, timeout management, failure verification, rollback
verification, operational metrics.

Scope (Foundation immutable):
- Minimal satu provider berjalan pada mode production.
- Retry tervalidasi.
- Timeout tervalidasi.
- Failure dapat diverifikasi.
- Rollback dapat diverifikasi.
- Jalur execution deterministik & auditable.

Tidak menambah authority. Mengintegrasikan komponen execution yang sudah ada
(retry/timeout limits, rollback runtime, metrics) dalam satu jalur production.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from .execution_request import ExecutionRequest
from .governed_execution import GovernedExecution, GovernedExecutionResult
from .execution_metrics import ExecutionMetrics
from .provider_selector import ProviderSelector


# ---------------------------------------------------------------------------
# Model (immutable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RetryOutcome:
    """Hasil percobaan retry (immutable)."""

    attempt: int
    status: str           # succeeded | failed | timeout | cancelled
    duration_ms: int = 0
    error: str = ""

    def as_dict(self) -> dict:
        return {"attempt": self.attempt, "status": self.status,
                "duration_ms": self.duration_ms, "error": self.error}


@dataclass(frozen=True)
class RollbackOutcome:
    """Hasil verifikasi rollback (immutable)."""

    rollback_requested: bool
    rolled_back: bool
    reversible: bool
    reason: str = ""

    def as_dict(self) -> dict:
        return {"rollback_requested": self.rollback_requested,
                "rolled_back": self.rolled_back, "reversible": self.reversible,
                "reason": self.reason}


@dataclass(frozen=True)
class ProductionExecutionResult:
    """Hasil eksekusi produksi (immutable)."""

    execution_id: str
    provider_id: str
    operation: str
    succeeded: bool
    final_status: str
    attempts: Tuple[RetryOutcome, ...] = field(default_factory=tuple)
    rollback: RollbackOutcome = field(default_factory=lambda: RollbackOutcome(False, False, False))
    metrics: Optional[ExecutionMetrics] = None
    governed: Optional[GovernedExecutionResult] = None
    elapsed_ms: int = 0

    def as_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "provider_id": self.provider_id,
            "operation": self.operation,
            "succeeded": self.succeeded,
            "final_status": self.final_status,
            "attempts": [a.as_dict() for a in self.attempts],
            "rollback": self.rollback.as_dict(),
            "metrics": self.metrics.as_dict() if self.metrics else None,
            "governed": self.governed.as_dict() if self.governed else None,
            "elapsed_ms": self.elapsed_ms,
        }


# ---------------------------------------------------------------------------
# Production execution engine
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProductionExecution:
    """Engine jalur produksi (read-only + orchestration terbatas).

    Melakukan: verifikasi kesiapan -> governed execute -> retry (bila gagal
    & dalam batas) -> verification -> rollback check -> metrics.
    Menghormati retry limit & timeout dari request (Article VII deterministik).
    """

    def __init__(
        self,
        governed: Optional[GovernedExecution] = None,
        selector: Optional[ProviderSelector] = None,
        max_retries_default: int = 2,
    ) -> None:
        self._governed = governed or GovernedExecution()
        self._selector = selector or ProviderSelector()
        self._max_retries_default = max_retries_default

    def _monotonic_ms(self) -> int:
        import time
        return int(time.time() * 1000)

    def run(self, request: ExecutionRequest,
            retry_limit: Optional[int] = None) -> ProductionExecutionResult:
        """Jalankan eksekusi produksi dengan retry & timeout management."""
        provider_id = request.provider_id
        operation = request.operation
        execution_id = request.execution_id
        max_retries = retry_limit if retry_limit is not None else \
            request.max_retries if request.max_retries is not None else self._max_retries_default
        started = self._monotonic_ms()
        attempts: List[RetryOutcome] = []
        final_status = "blocked"
        governed_result: Optional[GovernedExecutionResult] = None

        for attempt in range(1 + max_retries):
            attempt_start = self._monotonic_ms()
            req_attempt = ExecutionRequest(
                execution_id=execution_id,
                provider_id=provider_id,
                operation=operation,
                payload=dict(request.payload),
                mode=request.mode,
                timeout_seconds=request.timeout_seconds,
                max_retries=request.max_retries,
                cancellation_token=request.cancellation_token,
                approved=request.approved,
                approver=request.approver,
                deterministic=request.deterministic,
                synchronous=request.synchronous,
            )
            governed_result = self._governed.execute(req_attempt)
            outcome_status = self._state_from(governed_result)
            duration = self._monotonic_ms() - attempt_start
            attempts.append(RetryOutcome(
                attempt=attempt, status=outcome_status, duration_ms=duration,
                error=governed_result.evidence.status if not governed_result.executed else "",
            ))

            if outcome_status == "completed":
                final_status = "completed"
                break
            final_status = outcome_status

        elapsed = self._monotonic_ms() - started
        succeeded = final_status == "completed"
        metrics = ExecutionMetrics(
            metrics_id="m-{}".format(execution_id),
            execution_id=execution_id,
            duration_ms=elapsed,
            retries=len(attempts) - 1,
            external_calls=sum(1 for a in attempts if a.status == "completed"),
            size_payload=len(str(request.payload)),
        )
        rollback = self._evaluate_rollback(governed_result, succeeded)

        return ProductionExecutionResult(
            execution_id=execution_id,
            provider_id=provider_id,
            operation=operation,
            succeeded=succeeded,
            final_status=final_status,
            attempts=tuple(attempts),
            rollback=rollback,
            metrics=metrics,
            governed=governed_result,
            elapsed_ms=elapsed,
        )

    def _state_from(self, result: GovernedExecutionResult) -> str:
        """Ekstrak status akhir dari governed result (deterministik)."""
        if result.executed:
            return "completed"
        return result.evidence.status if result.evidence else "blocked"

    def _evaluate_rollback(self, result: Optional[GovernedExecutionResult],
                           succeeded: bool) -> RollbackOutcome:
        """Evaluasi apakah rollback perlu/ mungkin (verifikasi rollback).

        Rollback tidak di-eksekusi di sini (tanpa authority); hanya penilaian
        readiness & reversibilitas berbasis evidence.
        """
        if succeeded:
            return RollbackOutcome(False, False, True, reason="sukses, rollback tidak diperlukan")
        if result is None:
            return RollbackOutcome(False, False, False, reason="tidak ada hasil untuk rollback")
        reversible = result.evidence.external_calls > 0  # ada side-effect yang mungkin di-rollback
        return RollbackOutcome(
            rollback_requested=not succeeded,
            rolled_back=False,           # eksekusi rollback = kewenangan lain
            reversible=reversible,
            reason="gagal; rollback reversibel" if reversible else "gagal; tidak ada side-effect untuk dirollback",
        )
