"""Audit Runtime Registry — registri integrasi audit (Sprint 219).

Registri runtime yang diintegrasikan — metadata read-only, TIDAK mengubah
runtime lain. Menyimpan snapshot nama runtime dalam pipeline.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .audit_runtime_pipeline import INTEGRATION_ROUTE


@dataclass(frozen=True)
class AuditRuntimeRegistryEntry:
    """Entri registry integrasi (immutable)."""
    runtime: str = ""
    integrated: bool = True
    immutable: bool = True
    preview_only: bool = True


@dataclass(frozen=True)
class AuditRuntimeRegistry:
    """Registry runtime terintegrasi (immutable snapshot)."""
    entries: List[AuditRuntimeRegistryEntry] = field(default_factory=list)
    count: int = 0

    @classmethod
    def from_route(cls, route: List[str] = None) -> "AuditRuntimeRegistry":
        route = route or INTEGRATION_ROUTE
        entries = [
            AuditRuntimeRegistryEntry(runtime=r, integrated=True, immutable=True)
            for r in route
        ]
        return cls(entries=entries, count=len(entries))
