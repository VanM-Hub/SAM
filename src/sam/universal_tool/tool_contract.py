"""Tool Contract Model - WP-05 (MISSION-5.2 / IP-5.2-001).

Kontrak Tool seragam sebagai batas interaksi antara Tool Citizen dan SAM.
Bersifat declarative dan tidak mengandung execution logic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .tool_descriptor import ToolCapability, ToolCapabilityKind


@dataclass(frozen=True)
class ToolContract:
    """Kontrak tool yang menetapkan capability + boundary interaksi."""

    tool_id: str
    contract_id: str
    capabilities: Tuple[ToolCapability, ...] = field(default_factory=tuple)
    entry_points: Tuple[str, ...] = field(default_factory=tuple)
    requires_approval: bool = True
    requires_governance: bool = True
    supports_capability: Tuple[ToolCapabilityKind, ...] = field(default_factory=tuple)

    @property
    def governed(self) -> bool:
        return self.requires_governance or self.requires_approval

    def allows(self, kind: ToolCapabilityKind) -> bool:
        return kind in self.supports_capability

    def as_dict(self) -> dict:
        return {
            "tool_id": self.tool_id,
            "contract_id": self.contract_id,
            "capabilities": [c.as_dict() for c in self.capabilities],
            "entry_points": list(self.entry_points),
            "requires_approval": self.requires_approval,
            "requires_governance": self.requires_governance,
            "supports_capability": [k.value for k in self.supports_capability],
            "governed": self.governed,
        }
