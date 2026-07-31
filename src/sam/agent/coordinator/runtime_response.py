"""Runtime Response — response runtime (Sprint 160).

Agent Runtime — response read-only. Tidak mengeksekusi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class RuntimeResponse:
    """Response runtime (immutable, preview-only)."""
    request_id: str
    runtime_name: str
    ok: bool = True
    preview: bool = True
    external_calls: int = 0
    notes: List[str] = field(default_factory=list)
