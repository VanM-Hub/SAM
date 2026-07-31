# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 127 - Dependency Resolver: dependency_snapshot.

Immutable snapshot of the dependency graph at a point in time.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class DependencySnapshot:
    """Immutable snapshot of graph nodes and edges."""

    nodes: Tuple[str, ...] = field(default_factory=tuple)
    edges: Dict[str, Tuple[str, ...]] = field(default_factory=dict)

    @property
    def node_count(self) -> int:
        return len(self.nodes)
