"""Execution Request — frozen DTO request eksekusi."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ExecutionRequest:
    """Request eksekusi — permintaan untuk mengeksekusi task.

    Attributes:
        request_id: ID unik request.
        context_id: ID konteks terkait.
        timestamp: Waktu pembuatan (float).
        task_type: Jenis task (process, analyze, generate, transform).
        priority: Prioritas (1-10, 1 tertinggi).
        payload: Data payload request.
        tags: Tag untuk kategorisasi.
        metadata: Metadata tambahan.
    """
    request_id: str
    context_id: str
    timestamp: float
    task_type: str = "process"
    priority: int = 5
    payload: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
