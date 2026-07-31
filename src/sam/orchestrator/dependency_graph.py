# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 127 - Dependency Resolver: dependency_graph.

Directed graph of runtime dependencies. Sync, deterministic.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Set, Tuple


class DependencyGraph:
    """Graph where edges express "depends on" (read-only getters)."""

    def __init__(self) -> None:
        self._edges: Dict[str, Set[str]] = {}

    def add_edge(self, runtime: str, depends_on: str) -> None:
        """Declare that runtime depends on depends_on."""
        self._edges.setdefault(runtime, set()).add(depends_on)
        self._edges.setdefault(depends_on, set())

    def dependencies(self, runtime: str) -> FrozenSet[str]:
        """Runtimes that `runtime` depends on."""
        return frozenset(self._edges.get(runtime, set()))

    def dependents(self, runtime: str) -> FrozenSet[str]:
        """Runtimes that depend on `runtime`."""
        return frozenset(
            k for k, deps in self._edges.items() if runtime in deps
        )

    def all_nodes(self) -> FrozenSet[str]:
        return frozenset(self._edges.keys())

    def edge_count(self) -> int:
        return sum(len(d) for d in self._edges.values())
