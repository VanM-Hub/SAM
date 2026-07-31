"""Execution Preview — pipeline Preview -> Approval -> Execute (Sprint 237).

Preview-first, approval-gated, deterministic, immutable. Tanpa approval,
tidak ada eksekusi nyata; external_calls selalu 0 di preview.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ExecutionState(str, Enum):
    """Status eksekusi."""
    PREVIEW = "preview"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ExecutionRequest:
    """Request eksekusi (immutable)."""
    execution_id: str
    provider_id: str
    operation: str
    payload: Dict[str, Any] = field(default_factory=dict)
    state: ExecutionState = ExecutionState.PREVIEW
    external_calls: int = 0

    def as_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "provider_id": self.provider_id,
            "operation": self.operation,
            "payload": dict(self.payload),
            "state": self.state.value,
            "external_calls": self.external_calls,
        }


@dataclass(frozen=True)
class ExecutionApproval:
    """Keputusan approval (immutable)."""
    execution_id: str
    approved: bool
    reason: str = ""
    approved_by: str = "system"

    @property
    def is_approved(self) -> bool:
        return self.approved


@dataclass(frozen=True)
class ExecutionResult:
    """Hasil eksekusi (immutable)."""
    execution_id: str
    provider_id: str
    operation: str
    ok: bool = False
    preview: bool = True
    state: ExecutionState = ExecutionState.BLOCKED
    external_calls: int = 0
    detail: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


class ExecutionPipeline:
    """Pipeline Preview -> Approval -> Execute. Approval-gated, preview-first."""

    def __init__(self) -> None:
        self._pending: Dict[str, ExecutionRequest] = {}
        self._results: Dict[str, ExecutionResult] = {}

    def preview(self, request: ExecutionRequest) -> ExecutionResult:
        """Preview: simpan request, jangan eksekusi, external_calls=0."""
        self._pending[request.execution_id] = request
        return ExecutionResult(
            execution_id=request.execution_id,
            provider_id=request.provider_id,
            operation=request.operation,
            ok=True,
            preview=True,
            state=ExecutionState.AWAITING_APPROVAL,
            external_calls=0,
            detail="preview ready; menunggu approval",
            data={"preview": True},
        )

    def approve(self, approval: ExecutionApproval) -> ExecutionResult:
        """Approval: setujui request sebelum eksekusi nyata."""
        req = self._pending.get(approval.execution_id)
        if req is None:
            return ExecutionResult(
                execution_id=approval.execution_id,
                provider_id="unknown",
                operation="unknown",
                ok=False,
                preview=True,
                state=ExecutionState.BLOCKED,
                external_calls=0,
                detail="unknown execution",
            )
        if not approval.is_approved:
            return ExecutionResult(
                execution_id=req.execution_id,
                provider_id=req.provider_id,
                operation=req.operation,
                ok=False,
                preview=True,
                state=ExecutionState.REJECTED,
                external_calls=0,
                detail=approval.reason or "rejected",
            )
        # Approved -> siap eksekusi. Di sini kita belum melakukan network call.
        result = ExecutionResult(
            execution_id=req.execution_id,
            provider_id=req.provider_id,
            operation=req.operation,
            ok=True,
            preview=False,
            state=ExecutionState.APPROVED,
            external_calls=0,
            detail="approved; eksekusi diizinkan",
        )
        self._results[req.execution_id] = result
        return result

    def execute(self, execution_id: str, runner: Any = None) -> ExecutionResult:
        """Eksekusi nyata. TANPA approval -> BLOCKED. external_calls tetap 0 di sini."""
        req = self._pending.get(execution_id)
        if req is None:
            return ExecutionResult(
                execution_id=execution_id, provider_id="unknown",
                operation="unknown", ok=False, preview=True,
                state=ExecutionState.BLOCKED, external_calls=0,
                detail="unknown execution",
            )
        prior = self._results.get(execution_id)
        if prior is None or prior.state != ExecutionState.APPROVED:
            return ExecutionResult(
                execution_id=req.execution_id,
                provider_id=req.provider_id,
                operation=req.operation,
                ok=False,
                preview=True,
                state=ExecutionState.BLOCKED,
                external_calls=0,
                detail="eksekusi diblokir: belum ada approval",
            )
        # Sampai di sini, execution nyata memerlukan network/provider nyata.
        # Framework ini hanya menandai status; external_calls tetap 0.
        result = ExecutionResult(
            execution_id=req.execution_id,
            provider_id=req.provider_id,
            operation=req.operation,
            ok=True,
            preview=False,
            state=ExecutionState.COMPLETED,
            external_calls=0,
            detail="executed (framework preview)",
        )
        self._results[execution_id] = result
        return result

    def status(self, execution_id: str) -> Optional[ExecutionResult]:
        return self._results.get(execution_id)

    def pending_count(self) -> int:
        return len(self._pending)
