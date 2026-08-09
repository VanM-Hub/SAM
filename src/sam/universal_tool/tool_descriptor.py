"""Tool Descriptor & Capability Model - WP-03/WP-04 (MISSION-5.2 / IP-5.2-001).

Deskripsi Tool secara declarative + model capability Tool.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple

from .tool_identity import ToolIdentity


class ToolCapabilityKind(str, Enum):
    """Jenis kemampuan yang dapat dimiliki sebuah Tool."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    QUERY = "query"
    NOTIFY = "notify"
    TRANSFORM = "transform"


@dataclass(frozen=True)
class ToolCapability:
    """Satu capability Tool."""

    kind: ToolCapabilityKind
    name: str = ""
    detail: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"kind": self.kind.value, "name": self.name or self.kind.value, "detail": dict(self.detail)}


@dataclass(frozen=True)
class ToolDescriptor:
    """Deskripsi tool secara declarative."""

    identity: ToolIdentity
    capabilities: Tuple[ToolCapability, ...] = field(default_factory=tuple)
    interfaces: Tuple[str, ...] = field(default_factory=tuple)
    operational_metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    compatibility_metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def capability(self, kind: ToolCapabilityKind) -> Optional[ToolCapability]:
        for c in self.capabilities:
            if c.kind == kind:
                return c
        return None

    def as_dict(self) -> dict:
        return {
            "identity": self.identity.as_dict(),
            "capabilities": [c.as_dict() for c in self.capabilities],
            "interfaces": list(self.interfaces),
            "operational_metadata": dict(self.operational_metadata),
            "compatibility_metadata": dict(self.compatibility_metadata),
        }
