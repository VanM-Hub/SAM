"""Execution Preview Integration (Program A, Sprint 237).

Sprint 237 — Execution Preview Integration (OP-2410).
Pipeline eksplisit Preview -> Approval -> Execute untuk semua provider.
Default external_calls=0: tanpa approval, tidak ada eksekusi nyata.

Prinsip Program A:
- Preview: bangun payload, external_calls=0, deterministik.
- Approval: keputusan eksplisit (approved / rejected).
- Execute: HANYA berjalan setelah approval; tanpa approval, diblokir.
- Semua provider melalui interface yang sama. Immutable DTO.
"""
from .execution_preview import (
    ExecutionRequest,
    ExecutionApproval,
    ExecutionResult,
    ExecutionState,
    ExecutionPipeline,
)

__all__ = [
    "ExecutionRequest",
    "ExecutionApproval",
    "ExecutionResult",
    "ExecutionState",
    "ExecutionPipeline",
]
