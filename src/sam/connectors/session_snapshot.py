"""Session Snapshot — DTO snapshot sesi.

Sprint 116 — Connector Session.
Snapshot kondisi sesi pada satu titik (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class SessionSnapshot:
    """Snapshot sesi connector."""
    session_id: str
    state: str = "unknown"
    connector_id: str = ""
    captured_at_iso: str = ""
    extra: Dict[str, str] = field(default_factory=dict)
