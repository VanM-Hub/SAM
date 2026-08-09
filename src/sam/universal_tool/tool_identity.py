"""Tool Identity - WP-01 (MISSION-5.2 / IP-5.2-001).

Identity model untuk Tool Citizen. Identity immutable, bukan authority marker.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Tuple


class ToolType(str, Enum):
    """Klasifikasi jenis tool."""

    EXTERNAL = "external"
    LOCAL = "local"
    SDK = "sdk"
    PROCESS = "process"


class ToolStatus(str, Enum):
    """Status siklus hidup tool."""

    UNKNOWN = "unknown"
    REGISTERED = "registered"
    AVAILABLE = "available"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RETIRED = "retired"


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class ToolIdentity:
    """Identitas Tool Citizen yang stabil dan immutable."""

    tool_id: str
    name: str
    tool_type: ToolType = ToolType.EXTERNAL
    version: str = "1.0.0"
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    status: ToolStatus = ToolStatus.REGISTERED
    created_at: str = field(default_factory=_now_utc)

    @property
    def is_well_formed(self) -> bool:
        return bool(self.tool_id.strip()) and bool(self.name.strip())

    def as_dict(self) -> dict:
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "tool_type": self.tool_type.value,
            "version": self.version,
            "metadata": dict(self.metadata),
            "status": self.status.value,
            "created_at": self.created_at,
            "is_well_formed": self.is_well_formed,
        }
