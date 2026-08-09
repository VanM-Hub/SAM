"""Tool Request Model - WP-22 (MISSION-5.2 / IP-5.2-003).

Model request Tool yang diseragamkan dan immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Tuple

from .tool_descriptor import ToolCapabilityKind


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class ToolRequest:
    """Request invocation Tool (seragam, immutable)."""

    request_id: str
    tool_id: str
    capability: ToolCapabilityKind
    connector_id: str = ""
    parameters: Dict[str, object] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_utc)
    provenance: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "tool_id": self.tool_id,
            "capability": self.capability.value,
            "connector_id": self.connector_id,
            "parameters": dict(self.parameters),
            "created_at": self.created_at,
            "provenance": list(self.provenance),
        }
