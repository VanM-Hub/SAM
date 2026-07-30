"""Execution Candidate — frozen DTO kandidat eksekusi."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ExecutionCandidate:
    """Kandidat eksekusi — satu unit pekerjaan yang siap diplan.

    Attributes:
        candidate_id: ID unik kandidat.
        context_id: ID konteks terkait.
        request_id: ID request terkait.
        timestamp: Waktu pembuatan (float).
        name: Nama kandidat.
        description: Deskripsi singkat.
        candidate_type: Jenis kandidat (task, subprocess, batch).
        estimated_effort: Estimasi effort (jam, menit).
        dependencies: Daftar ID kandidat yang menjadi dependensi.
        tags: Tag untuk kategorisasi.
        metadata: Metadata tambahan.
    """
    candidate_id: str
    context_id: str
    request_id: str
    timestamp: float
    name: str = ""
    description: str = ""
    candidate_type: str = "task"
    estimated_effort: float = 0.0
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
