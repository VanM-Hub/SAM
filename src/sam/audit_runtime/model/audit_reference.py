"""Audit Reference — referensi provenance audit (Sprint 213)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class AuditReference:
    """Referensi provenance immutable — jejak asal-usul."""
    ref_id: str
    kind: str = "provenance"
    source: str = ""
    commit_hash: str = ""
    traceable: bool = True

    def __post_init__(self) -> None:
        if not self.ref_id.strip():
            raise ValueError("ref_id cannot be empty")
