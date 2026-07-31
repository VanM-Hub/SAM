"""Mission Session — sesi mission (immutable DTO, Sprint 157).

Agent Runtime — sesi merepresentasikan satu mission aktif. Preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class MissionSession:
    """Sesi mission (immutable)."""
    session_id: str
    mission_id: str
    agent_id: str
    open: bool = True
    active: bool = True
    external_calls: int = 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "session_id": self.session_id,
            "mission_id": self.mission_id,
            "agent_id": self.agent_id,
            "open": self.open,
            "active": self.active,
            "external_calls": self.external_calls,
        }
