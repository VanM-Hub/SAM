"""Audit Contract — kontrak audit (Sprint 212)."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuditContract:
    """Kontrak audit immutable. Menjamin sifat deterministic preview-only."""
    immutable: bool = True
    preview_only: bool = True
    no_write: bool = True
    no_execute: bool = True
    deterministic_hash: str = "sha256"
    guarantees: tuple = field(default=(
        "immutable",
        "preview_only",
        "no_write",
        "no_execute",
        "deterministic",
    ))
