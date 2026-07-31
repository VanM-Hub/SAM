"""RuntimeServiceMetadata (Sprint 261).

Program D - Runtime Services & Deployment.
Immutable metadata for a runtime service.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class RuntimeServiceMetadata:
    """Metadata service runtime (immutable)."""
    service_id: str
    name: str
    version: str = "27.0.0"
    runtime_version: str = "27.0.0"
    created_at: str = "2026-08-01"
    architecture: str = "runtime-service"
    labels: Dict[str, str] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.service_id:
            raise ValueError("service_id is required")
        if not self.name:
            raise ValueError("name is required")

    def as_dict(self) -> dict:
        return {
            "service_id": self.service_id,
            "name": self.name,
            "version": self.version,
            "runtime_version": self.runtime_version,
            "created_at": self.created_at,
            "architecture": self.architecture,
            "labels": dict(self.labels),
            "capabilities": list(self.capabilities),
        }
