"""Execution Context — frozen DTO konteks eksekusi."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ExecutionContext:
    """Konteks eksekusi — informasi lengkap untuk memulai eksekusi.

    Attributes:
        context_id: ID unik konteks.
        timestamp: Waktu pembuatan (float).
        source_activation: ID Activation Package yang menjadi sumber.
        environment: Lingkungan target (normal, restricted, critical).
        total_tasks: Jumlah task yang akan dieksekusi.
        total_steps: Jumlah step keseluruhan.
        decision_id: ID decision terkait (opsional).
        approval_id: ID approval terkait (opsional).
        metadata: Metadata tambahan.
    """
    context_id: str
    timestamp: float
    source_activation: str = ""
    environment: str = "normal"
    total_tasks: int = 0
    total_steps: int = 0
    decision_id: Optional[str] = None
    approval_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
