"""Execution Runtime (Sprint 254).

Program C - Real Execution Runtime.
Runtime facade di atas ExecutionPipeline: request masuk -> pipeline -> hasil.
Synchronous, approval-gated, preview-clean.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from .execution_request import ExecutionRequest
from .execution_response import ExecutionResponse
from .execution_pipeline import ExecutionPipeline, ExecutionPipelineResult
from .approval_gate import ApprovalGate


@dataclass(frozen=True)
class ExecutionOutcome:
    """Hasil runtime eksekusi (immutable)."""
    runtime_id: str
    result: ExecutionPipelineResult
    approved: bool = False
    executed: bool = False
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "approved": self.approved,
            "executed": self.executed,
            "external_calls": self.external_calls,
            "response": self.result.response.as_dict(),
        }


class ExecutionRuntime:
    """Runtime eksekusi. Facade synchronous."""

    def __init__(self, pipeline: ExecutionPipeline | None = None,
                 gate: ApprovalGate | None = None) -> None:
        self._pipeline = pipeline or ExecutionPipeline()
        self._gate = gate or ApprovalGate()

    @property
    def pipeline(self) -> ExecutionPipeline:
        return self._pipeline

    def run(self, runtime_id: str, request: ExecutionRequest) -> ExecutionOutcome:
        result = self._pipeline.run(f"{runtime_id}-pipe", request)
        approved = self._gate.may_execute(request)
        return ExecutionOutcome(
            runtime_id=runtime_id,
            result=result,
            approved=approved,
            executed=result.executed,
            external_calls=result.external_calls,
        )
