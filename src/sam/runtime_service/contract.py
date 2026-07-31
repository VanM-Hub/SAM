"""RuntimeServiceContract (Sprint 261).

Program D - Runtime Services & Deployment.
Immutable contract describing how a runtime service behaves.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class RuntimeServiceContract:
    """Kontrak service runtime (immutable). Sync, deterministic."""
    service: str
    version: str = "27.0.0"
    immutable: bool = True
    synchronous: bool = True
    deterministic: bool = True
    network_allowed: bool = False
    approval_required: bool = True
    preview_first: bool = True
    layers: List[str] = field(default_factory=list)
    additional_properties: bool = False

    def __post_init__(self) -> None:
        if not self.service:
            raise ValueError("service is required")
        if self.network_allowed:
            raise ValueError("runtime service contract is local-only; no network")

    def validate(self) -> bool:
        """Cek kontrak ini sesuai dengan prinsip Program D."""
        if self.immutable and self.synchronous and self.deterministic:
            return not self.network_allowed
        return False

    def as_dict(self) -> dict:
        return {
            "service": self.service,
            "version": self.version,
            "immutable": self.immutable,
            "synchronous": self.synchronous,
            "deterministic": self.deterministic,
            "network_allowed": self.network_allowed,
            "approval_required": self.approval_required,
            "preview_first": self.preview_first,
            "layers": list(self.layers),
            "additional_properties": self.additional_properties,
        }
