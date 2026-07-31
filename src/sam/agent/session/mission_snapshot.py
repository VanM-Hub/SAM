"""Mission Snapshot — snapshot mission (immutable DTO, Sprint 157).

Agent Runtime — snapshot adalah potret state mission pada satu titik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class MissionSnapshot:
    """Snapshot mission (immutable)."""
    mission_id: str
    state: str = "Created"
    session_id: Optional[str] = None
    detail: Dict[str, Any] = field(default_factory=dict)
