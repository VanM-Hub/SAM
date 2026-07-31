"""Workflow Runtime Registry — registri integrasi workflow (Sprint 203).

Registri runtime yang diintegrasikan — metadata read-only, TIDAK mengubah
runtime lain. Menyimpan snapshot nama runtime dalam pipeline.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict

from .workflow_runtime_pipeline import INTEGRATION_ROUTE


@dataclass(frozen=True)
class WorkflowRuntimeRegistryEntry:
    """Entri registry integrasi (immutable)."""
    runtime: str = ""
    integrated: bool = True
    preview_only: bool = True


@dataclass(frozen=True)
class WorkflowRuntimeRegistry:
    """Registry runtime terintegrasi (immutable snapshot)."""
    entries: List[WorkflowRuntimeRegistryEntry] = field(default_factory=list)
    count: int = 0

    @classmethod
    def from_route(cls, route: List[str] = None) -> "WorkflowRuntimeRegistry":
        route = route or INTEGRATION_ROUTE
        entries = [
            WorkflowRuntimeRegistryEntry(runtime=r, integrated=True)
            for r in route
        ]
        return cls(entries=entries, count=len(entries))
