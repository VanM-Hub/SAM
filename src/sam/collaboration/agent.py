"""Agent Model — Sprint 26 Fase 1.

Represents a SAM agent in the collaboration ecosystem.
An agent is any runtime instance registered in the ecosystem
with its own capabilities, status, and endpoint.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


AGENT_STATUSES = frozenset({"ONLINE", "OFFLINE", "BUSY", "IDLE"})


class Agent:
    """A registered agent in the SAM collaboration ecosystem.

    Each agent represents a runtime instance with specific capabilities,
    a network endpoint, and a current operational status.
    """

    def __init__(
        self,
        id: str,
        name: str,
        endpoint: str,
        capabilities: Optional[List[str]] = None,
        status: str = "ONLINE",
        metadata: Optional[Dict[str, Any]] = None,
        last_heartbeat: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        if status not in AGENT_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of {sorted(AGENT_STATUSES)}"
            )
        self.id = id
        self.name = name
        self.endpoint = endpoint
        self.capabilities = capabilities or []
        self.status = status
        self.metadata = metadata or {}
        now = datetime.now(timezone.utc)
        self.last_heartbeat = last_heartbeat or now
        self.created_at = created_at or now

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "capabilities": json.dumps(self.capabilities),
            "status": self.status,
            "endpoint": self.endpoint,
            "metadata": json.dumps(self.metadata),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Agent:
        return cls(
            id=data["id"],
            name=data["name"],
            endpoint=data["endpoint"],
            capabilities=_parse_list_str(data.get("capabilities", "[]")),
            status=data.get("status", "ONLINE"),
            metadata=_parse_json_dict(data.get("metadata", "{}")),
            last_heartbeat=_parse_dt(data.get("last_heartbeat")),
            created_at=_parse_dt(data.get("created_at")),
        )

    def __repr__(self) -> str:
        return (
            f"Agent(id={self.id!r}, name={self.name!r}, "
            f"status={self.status!r}, endpoint={self.endpoint!r})"
        )


def _parse_list_str(val: Any) -> List[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(v) for v in val]
    try:
        parsed = json.loads(val)
        return [str(v) for v in parsed] if isinstance(parsed, list) else []
    except (ValueError, TypeError):
        return []


def _parse_json_dict(val: Any) -> Dict[str, Any]:
    if val is None:
        return {}
    if isinstance(val, dict):
        return val
    try:
        parsed = json.loads(val)
        return parsed if isinstance(parsed, dict) else {}
    except (ValueError, TypeError):
        return {}


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        return None
