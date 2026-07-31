"""Filesystem Response — frozen DTO hasil preview filesystem.

Sprint 145 — Filesystem Provider.
Hasil preview (simulasi) — tidak ada hasil eksekusi disk nyata.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class FilesystemResponse:
    """Response operasi filesystem (immutable)."""
    request_id: str
    operation: str
    ok: bool = True
    preview: bool = True
    external_calls: int = 0
    message: str = ""
    entries: List[str] = field(default_factory=list)  # untuk list
    detail: Optional[str] = None
