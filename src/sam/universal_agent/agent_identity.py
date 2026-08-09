"""Agent Identity - WP-01 (MISSION-5.3 / IP-5.3-001).

Identity model untuk Agent Citizen. Immutable, bukan authority marker.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Tuple


class AgentType(str, Enum):
    """Klasifikasi jenis agent."""

    EXTERNAL = "external"
    SUBAGENT = "subagent"
    ORCHESTRATOR = "orchestrator"
    WORKER = "worker"


class AgentStatus(str, Enum):
    """Status siklus hidup agent."""

    UNKNOWN = "unknown"
    REGISTERED = "registered"
    AVAILABLE = "available"
    ACTIVE = "active"
    DEGRADED = "degraded"
    RETIRED = "retired"


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class AgentIdentity:
    """Identitas Agent Citizen yang stabil dan immutable."""

    agent_id: str
    name: str
    agent_type: AgentType = AgentType.EXTERNAL
    version: str = "1.0.0"
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    status: AgentStatus = AgentStatus.REGISTERED
    created_at: str = field(default_factory=_now_utc)

    @property
    def is_well_formed(self) -> bool:
        return bool(self.agent_id.strip()) and bool(self.name.strip())

    def as_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "agent_type": self.agent_type.value,
            "version": self.version,
            "metadata": dict(self.metadata),
            "status": self.status.value,
            "created_at": self.created_at,
            "is_well_formed": self.is_well_formed,
        }
