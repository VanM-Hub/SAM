"""RuntimeServiceDescriptor (Sprint 261).

Program D - Runtime Services & Deployment.
Immutable, deterministic description of a runtime service.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class RuntimeServiceDescriptor:
    """Deskripsi service runtime (immutable). Read-only, no network."""
    name: str
    service_type: str = "runtime"  # runtime | server | api | monitor
    phase: str = "xxvii"
    version: str = "27.0.0"
    description: str = ""
    requires_configuration: bool = True
    requires_secrets: bool = False
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name is required")
        valid_types = ("runtime", "server", "api", "monitor")
        if self.service_type not in valid_types:
            raise ValueError(f"service_type must be one of {valid_types}")

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "service_type": self.service_type,
            "phase": self.phase,
            "version": self.version,
            "description": self.description,
            "requires_configuration": self.requires_configuration,
            "requires_secrets": self.requires_secrets,
            "dependencies": list(self.dependencies),
            "tags": list(self.tags),
        }
