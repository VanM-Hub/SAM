"""Session Context — DTO konteks sesi connector.

Sprint 116 — Connector Session.
Konteks sesi murni, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class SessionContext:
    """Konteks sebuah sesi connector."""
    session_id: str
    connector_id: str
    binding_id: str = ""
    state: str = "created"  # created | active | closed
    variables: Dict[str, str] = field(default_factory=dict)
