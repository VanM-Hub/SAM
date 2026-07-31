# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 127 - Dependency Resolver: conversation_dependency.

Read-only conversation bridge for dependency resolution.
"""
from __future__ import annotations

from typing import Dict, Tuple

from .dependency_graph import DependencyGraph
from .dependency_resolver import DependencyResolver
from .dependency_report import DependencyReport


class ConversationDependencyBridge:
    """Read-only bridge exposing dependency resolution."""

    def __init__(self, graph: DependencyGraph) -> None:
        self._graph = graph
        self._resolver = DependencyResolver(graph)

    def resolve(self) -> Tuple[str, ...]:
        return self._resolver.resolve()

    def report(self) -> DependencyReport:
        return DependencyReport(
            order=self._resolver.resolve(),
            acyclic=not self._resolver.has_cycle(),
            edge_count=self._graph.edge_count(),
        )

    def has_cycle(self) -> bool:
        return self._resolver.has_cycle()

    def summary(self) -> Dict[str, int]:
        return {
            "nodes": len(self._graph.all_nodes()),
            "edges": self._graph.edge_count(),
        }
