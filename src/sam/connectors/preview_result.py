"""Preview Result — DTO hasil preview.

Sprint 119 — Connector Preview.
Hasil preview simulasi — tidak ada eksekusi eksternal.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass(frozen=True)
class PreviewResult:
    """Hasil preview (simulasi)."""
    preview_id: str
    connector_id: str
    operation: str = "read"
    success: bool = False
    simulated_effects: List[str] = field(default_factory=list)
    external_calls: int = 0  # harus selalu 0
    message: str = ""
