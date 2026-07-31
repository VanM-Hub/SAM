"""Execution Pipeline (Sprint 254).

Program C - Real Execution Runtime.
Pipeline: Request -> Validation -> Approval -> Dispatch -> Provider ->
Response -> Report.

Provider call dilakukan HANYA pada mode execute dengan approval valid,
melalui executor generik (abstraksi, bukan provider-specific). Network pada
preview = 0. Synchronous.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional

from .execution_request import ExecutionRequest
from .execution_response import ExecutionResponse
from .execution_validation import ExecutionValidationEngine, ExecutionValidation
from .approval_pipeline import ApprovalPipeline, ApprovalPipelineResult
from .provider_pipeline import ProviderPipeline, ProviderPipelineResult
from .execution_report import ExecutionReport, StageTrace


class _ProviderExecutor:
    """Abstraksi pemanggil provider (generic). Di-suntik dari luar.

    Contract: call(request) -> ExecutionResponse. Network hanya bermakna
    pada mode execute yang sudah di-approve.
    """

    def __init__(self) -> None:
        self._handler: Optional[Callable[[ExecutionRequest], ExecutionResponse]] = None

    def bind(self, handler: Callable[[ExecutionRequest], ExecutionResponse]) -> None:
        self._handler = handler

    def call(self, request: ExecutionRequest) -> ExecutionResponse:
        if self._handler is None:
            return ExecutionResponse(
                execution_id=request.execution_id,
                provider_id=request.provider_id,
                operation=request.operation,
                status="failed",
                mode=request.mode,
                external_calls=0,
                error="no provider executor bound",
            )
        return self._handler(request)


@dataclass(frozen=True)
class ExecutionPipelineResult:
    """Hasil pipeline (immutable)."""
    pipeline_id: str
    execution_id: str
    validation: ExecutionValidation
    approval: ApprovalPipelineResult
    provider: ProviderPipelineResult
    response: ExecutionResponse
    report: ExecutionReport
    executed: bool = False
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "pipeline_id": self.pipeline_id,
            "execution_id": self.execution_id,
            "validation": self.validation.as_dict(),
            "approval": self.approval.as_dict(),
            "provider": self.provider.as_dict(),
            "response": self.response.as_dict(),
            "report": self.report.as_dict(),
            "executed": self.executed,
            "external_calls": self.external_calls,
        }


STAGES = (
    "request", "validation", "approval", "dispatch", "provider", "response", "report",
)


class ExecutionPipeline:
    """Pipeline eksekusi. Synchronous, no network di preview."""

    def __init__(self, validation_engine: ExecutionValidationEngine | None = None,
                 approval: ApprovalPipeline | None = None,
                 provider: ProviderPipeline | None = None,
                 executor: _ProviderExecutor | None = None) -> None:
        self._validation = validation_engine or ExecutionValidationEngine()
        self._approval = approval or ApprovalPipeline()
        self._provider = provider or ProviderPipeline()
        self._executor = executor or _ProviderExecutor()

    @property
    def executor(self) -> _ProviderExecutor:
        return self._executor

    def run(self, pipeline_id: str, request: ExecutionRequest) -> ExecutionPipelineResult:
        traces: list = [StageTrace("request", "ok", 0)]
        # 1. Validation
        validation = self._validation.validate(f"v-{pipeline_id}", request)
        traces.append(StageTrace("validation", "ok" if validation.valid else "failed", 0,
                                 detail="valid" if validation.valid else ";".join(validation.errors)))
        # 2. Approval
        approval = self._approval.run(f"ap-{pipeline_id}", request)
        traces.append(StageTrace("approval", "ok" if approval.state != "blocked" else "blocked", 0,
                                 detail=approval.state))
        # 3. Dispatch
        provider = self._provider.run(f"pp-{pipeline_id}", request)
        traces.append(StageTrace("dispatch", "ok", 0))
        # 4. Provider (execute-only, gated oleh approval)
        executed = False
        response: ExecutionResponse
        if request.mode == "execute" and approval.approved and validation.valid:
            response = self._executor.call(request)
            executed = response.status not in ("failed", "cancelled", "timeout")
            traces.append(StageTrace("provider", "ok" if executed else response.status,
                                     response.external_calls, detail=response.status))
        else:
            response = ExecutionResponse(
                execution_id=request.execution_id,
                provider_id=request.provider_id,
                operation=request.operation,
                status="preview" if request.mode != "execute" else "blocked",
                mode=request.mode,
                external_calls=0,
            )
            traces.append(StageTrace("provider", "ok", 0, detail=response.status))
        # 5. Response
        traces.append(StageTrace("response", "ok", 0))
        # 6. Report (trace terakhir, setelah semua stage)
        status = "completed" if response.status == "completed" else (
            "failed" if response.status in ("failed", "timeout", "cancelled") else "pending")
        traces.append(StageTrace("report", "ok", 0))
        report = ExecutionReport(
            report_id=f"rp-{pipeline_id}",
            execution_id=request.execution_id,
            stages=tuple(traces),
            status=status,
            external_calls=response.external_calls,
        )
        total_calls = response.external_calls
        if request.mode != "execute":
            total_calls = 0
        return ExecutionPipelineResult(
            pipeline_id=pipeline_id,
            execution_id=request.execution_id,
            validation=validation,
            approval=approval,
            provider=provider,
            response=response,
            report=report,
            executed=executed,
            external_calls=total_calls,
        )
