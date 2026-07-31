"""Audit Manifest — manifest sertifikasi audit (Sprint 218)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class AuditManifest:
    """Manifest immutable."""
    version: str = "22.0.0"
    runtime: str = "audit_runtime"
    subsystems: Tuple[str, ...] = field(default_factory=tuple)
    no_inference: bool = True
    no_write: bool = True
    no_execute: bool = True
    immutable: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "subsystems", self.subsystems or (
            "foundation", "model", "builder", "runtime", "catalog",
            "monitoring", "certification", "integration", "dashboard",
        ))
