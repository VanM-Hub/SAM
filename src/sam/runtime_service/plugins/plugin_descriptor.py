"""PluginDescriptor (Sprint 266).

Program D - Runtime Services & Deployment.
Deskripsi plugin (immutable). Hanya metadata.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class PluginDescriptor:
    """Deskripsi plugin (immutable). Metadata only, no behavior."""
    name: str
    version: str = "1.0.0"
    kind: str = "provider"  # provider | tool | integration
    secret_key: Optional[str] = None
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    requires_configuration: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required")

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "kind": self.kind,
            "secret_key": self.secret_key,
            "description": self.description,
            "capabilities": list(self.capabilities),
            "requires_configuration": self.requires_configuration,
        }
