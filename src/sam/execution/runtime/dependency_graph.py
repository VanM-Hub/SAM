"""Dependency Graph — frozen DTO grafik dependensi."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class DependencyNode:
    """Node dalam dependency graph."""
    candidate_id: str
    depends_on: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DependencyGraph:
    """Grafik dependensi — hubungan antar kandidat."""
    nodes: Dict[str, DependencyNode] = field(default_factory=dict)
    edges: int = 0
    levels: int = 0


@dataclass(frozen=True)
class DependencyValidation:
    """Hasil validasi dependensi."""
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    total_dependencies: int = 0


@dataclass(frozen=True)
class ExecutionOrder:
    """Urutan eksekusi berdasarkan dependensi."""
    order_id: str
    ordered_candidate_ids: Tuple[str, ...] = field(default_factory=tuple)
    levels: List[Tuple[str, ...]] = field(default_factory=list)
    total_levels: int = 0
    has_cycles: bool = False


@dataclass(frozen=True)
class DependencySummary:
    """Ringkasan dependensi."""
    total_nodes: int = 0
    total_edges: int = 0
    max_depth: int = 0
    has_cycles: bool = False
    status: str = "empty"
