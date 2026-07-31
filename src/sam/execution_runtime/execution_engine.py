"""Execution Engine (Sprint 254).

Program C - Real Execution Runtime.
Engine adalah titik masuk utama eksekusi. Menerima request, menjalankan
pipeline, dan menegakkan aturan immutability/preview/approval. Tidak ada
provider-specific logic di sini.
"""
from __future__ import annotations
from typing import Optional

from .execution_runtime import ExecutionRuntime, ExecutionOutcome
from .execution_request import ExecutionRequest
from .execution_pipeline import ExecutionPipeline
from .execution_report import ExecutionReport
from .execution_summary import ExecutionSummary


class ExecutionEngine:
    """Execution Engine (front facade)."""

    def __init__(self, runtime: ExecutionRuntime | None = None) -> None:
        self._runtime = runtime or ExecutionRuntime()
        self._summary = ExecutionSummary()

    @property
    def runtime(self) -> ExecutionRuntime:
        return self._runtime

    def execute(self, request: ExecutionRequest) -> ExecutionOutcome:
        outcome = self._runtime.run(f"eng-{request.execution_id}", request)
        self._summary = self._summary.add(outcome.result.report)
        return outcome

    def summary(self) -> dict:
        return self._summary.to_dict()
