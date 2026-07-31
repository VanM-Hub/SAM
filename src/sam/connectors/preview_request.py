"""Preview Request — DTO permintaan preview.

Sprint 119 — Connector Preview.
Preview = simulasi eksekusi. TIDAK pernah mengirim ke sistem luar.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class PreviewRequest:
    """Permintaan preview untuk connector."""
    preview_id: str
    connector_id: str
    operation: str = "read"
    neutral_payload: Dict[str, Any] = field(default_factory=dict)
    dry_run: bool = True  # selalu True — preview-only
