"""Mission Context — konteks mission (immutable DTO, Sprint 157).

Agent Runtime — konteks membawa data read-only untuk lifecycle mission.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class MissionContext:
    """Konteks mission (immutable)."""
    mission_id: str
    agent_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    created_by: str = "agent"
    readonly: bool = True

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)
