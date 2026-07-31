"""Audit Runtime Manifest — manifest integrasi (Sprint 219)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AuditRuntimeManifest:
    """Manifest runtime integrasi (immutable)."""
    version: str = "22.0.0"
    runtime: str = "audit_runtime"
    integrated_runtimes: List[str] = field(default_factory=list)
    preview_only: bool = True
    no_inference: bool = True
    no_execute: bool = True
    immutable: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "integrated_runtimes",
            self.integrated_runtimes or [
                "mission", "agent", "skill", "workflow", "policy", "memory",
                "knowledge", "cognitive", "orchestrator", "connector",
                "provider",
            ],
        )
