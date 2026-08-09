"""Tool Registry - WP-02 (MISSION-5.2 / IP-5.2-001).

Registry sebagai sumber discovery Tool Citizen. Registry tidak melakukan
execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

from .tool_identity import ToolIdentity, ToolStatus


@dataclass(frozen=True)
class ToolRegistryEntry:
    """Entri registry satu tool."""

    identity: ToolIdentity
    registered_at: str
    availability: bool = False

    def as_dict(self) -> dict:
        return {
            "identity": self.identity.as_dict(),
            "registered_at": self.registered_at,
            "availability": self.availability,
        }


class ToolRegistry:
    """Registry Tool Citizen (read/discovery, bukan execution)."""

    def __init__(self) -> None:
        self._tools: dict = {}

    def register(self, identity: ToolIdentity, availability: bool = False) -> ToolRegistryEntry:
        entry = ToolRegistryEntry(
            identity=identity,
            registered_at=datetime.utcnow().isoformat() + "Z",
            availability=availability,
        )
        self._tools[identity.tool_id] = entry
        return entry

    def remove(self, tool_id: str) -> bool:
        return self._tools.pop(tool_id, None) is not None

    def lookup(self, tool_id: str) -> Optional[ToolIdentity]:
        entry = self._tools.get(tool_id)
        return entry.identity if entry else None

    def set_availability(self, tool_id: str, available: bool) -> bool:
        entry = self._tools.get(tool_id)
        if entry is None:
            return False
        self._tools[tool_id] = ToolRegistryEntry(
            identity=entry.identity,
            registered_at=entry.registered_at,
            availability=available,
        )
        return True

    def list(self, status: Optional[ToolStatus] = None) -> Tuple[ToolIdentity, ...]:
        items = tuple(e.identity for e in self._tools.values())
        if status is not None:
            items = tuple(i for i in items if i.status == status)
        return items

    def available(self) -> Tuple[ToolIdentity, ...]:
        return tuple(e.identity for e in self._tools.values() if e.availability)

    def size(self) -> int:
        return len(self._tools)

    def validate_registry(self) -> bool:
        return all(e.identity.is_well_formed for e in self._tools.values())
