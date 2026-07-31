"""Policy Runtime Registry — registri integrasi policy (Sprint 211).

Registri runtime yang diintegrasikan — metadata read-only, TIDAK mengubah
runtime lain. Menyimpan snapshot nama runtime dalam pipeline.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .policy_runtime_pipeline import INTEGRATION_ROUTE


@dataclass(frozen=True)
class PolicyRuntimeRegistryEntry:
    """Entri registry integrasi (immutable)."""
    runtime: str = ""
    integrated: bool = True
    preview_only: bool = True


@dataclass(frozen=True)
class PolicyRuntimeRegistry:
    """Registry runtime terintegrasi (immutable snapshot)."""
    entries: List[PolicyRuntimeRegistryEntry] = field(default_factory=list)
    count: int = 0

    @classmethod
    def from_route(cls, route: List[str] = None) -> "PolicyRuntimeRegistry":
        route = route or INTEGRATION_ROUTE
        entries = [
            PolicyRuntimeRegistryEntry(runtime=r, integrated=True)
            for r in route
        ]
        return cls(entries=entries, count=len(entries))
