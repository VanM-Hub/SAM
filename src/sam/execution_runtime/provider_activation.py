"""Real Provider Activation (Sprint 260).

Program C - Real Execution Runtime.
Menjembatani Execution Runtime ke provider layer (Sprint 260).

FILE INI DI EXECUTION_RUNTIME TIDAK berisi provider-specific logic --- ia
men-delegate ke `src/sam/providers/execution/provider_executor.py` (provider
layer) lewat kontrak generik. Network & kredensial HANYA di provider layer.

Alur: request execute+approved -> delegasi ke ProviderExecutor -> hasil.
Provider unavailable => error dibungkus ke ExecutionResponse status=failed.
"""
from __future__ import annotations
from typing import Any, Dict

from .execution_request import ExecutionRequest
from .execution_response import ExecutionResponse
from .execution_pipeline import _ProviderExecutor
from ..providers.execution.provider_executor import (
    ProviderExecutor as RealProviderExecutor, ProviderUnavailableError,
)


class ProviderActivationExecutor(_ProviderExecutor):
    """Delegator eksekusi ke provider layer. Approve-gated oleh caller."""

    def __init__(self, real: RealProviderExecutor | None = None) -> None:
        super().__init__()
        self._real = real or RealProviderExecutor()
        self._cancelled_tokens: set = set()

    def cancel_token(self, token: str) -> None:
        """Tandai token untuk pembatalan (synchronous check point)."""
        self._cancelled_tokens.add(token)

    def _is_cancelled(self, request: ExecutionRequest) -> bool:
        if not request.cancellation_token:
            return False
        return request.cancellation_token in self._cancelled_tokens

    def call(self, request: ExecutionRequest) -> ExecutionResponse:
        # Pastikan hanya execute yang di-delegasikan (guard dipanggil caller).
        if request.mode != "execute":
            return ExecutionResponse(
                execution_id=request.execution_id,
                provider_id=request.provider_id,
                operation=request.operation,
                status="preview",
                mode=request.mode,
                external_calls=0,
            )
        # approval dijaga oleh pipeline; ini asuransi ganda
        if not request.approved:
            return ExecutionResponse(
                execution_id=request.execution_id,
                provider_id=request.provider_id,
                operation=request.operation,
                status="blocked",
                mode=request.mode,
                external_calls=0,
                error="execute tanpa approval",
            )
        # cancellation check
        if self._is_cancelled(request):
            return ExecutionResponse(
                execution_id=request.execution_id,
                provider_id=request.provider_id,
                operation=request.operation,
                status="cancelled",
                mode=request.mode,
                external_calls=0,
                error="execution cancelled",
            )
        if not self._real.available(request.provider_id):
            return ExecutionResponse(
                execution_id=request.execution_id,
                provider_id=request.provider_id,
                operation=request.operation,
                status="failed",
                mode=request.mode,
                external_calls=0,
                error=f"provider unavailable: {request.provider_id}",
            )
        try:
            result = self._real.execute(
                request.provider_id, request.operation,
                payload=dict(request.payload),
                timeout_seconds=request.timeout_seconds,
            )
            return ExecutionResponse(
                execution_id=request.execution_id,
                provider_id=request.provider_id,
                operation=request.operation,
                status=result.get("status", "completed"),
                payload=result.get("payload", {}),
                mode=request.mode,
                external_calls=result.get("external_calls", 1),
            )
        except ProviderUnavailableError as exc:
            return ExecutionResponse(
                execution_id=request.execution_id,
                provider_id=request.provider_id,
                operation=request.operation,
                status="failed",
                mode=request.mode,
                external_calls=0,
                error=str(exc),
            )
        except Exception as exc:  # noqa: BLE001 - error propagation
            return ExecutionResponse(
                execution_id=request.execution_id,
                provider_id=request.provider_id,
                operation=request.operation,
                status="failed",
                mode=request.mode,
                external_calls=0,
                error=f"execution error: {exc}",
            )
