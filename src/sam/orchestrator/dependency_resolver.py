# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 127 - Dependency Resolver: dependency_resolver.

Resolves a topological order of runtimes given dependency graph.
Arranges order - never executes.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from .dependency_graph import DependencyGraph


class DependencyResolver:
    """Produces a deterministic topological ordering."""

    def __init__(self, graph: DependencyGraph) -> None:
        self._graph = graph

    def resolve(self) -> Tuple[str, ...]:
        """Return runtimes in dependency order (dependencies first)."""
        order: List[str] = []
        visited: set = set()
        temporary: set = set()

        def visit(node: str) -> None:
            if node in temporary:
                raise ValueError("dependency cycle at {0}".format(node))
            if node in visited:
                return
            temporary.add(node)
            for dep in sorted(self._graph.dependencies(node)):
                visit(dep)
            temporary.discard(node)
            visited.add(node)
            order.append(node)

        for node in sorted(self._graph.all_nodes()):
            visit(node)
        return tuple(order)

    def has_cycle(self) -> bool:
        try:
            self.resolve()
            return False
        except ValueError:
            return True
