"""Conversation Dependencies Bridge — 8 queries."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from sam.execution.runtime.dependency_graph import DependencyGraph
from sam.execution.runtime.dependency_resolver import (
    DependencyGraphBuilder, DependencyValidator, ExecutionOrderResolver,
)


class ConversationDependencies:
    """Conversation bridge untuk execution dependencies — 8 queries."""

    def __init__(self, graph_builder: DependencyGraphBuilder,
                 validator: DependencyValidator,
                 resolver: ExecutionOrderResolver) -> None:
        self._graph_builder = graph_builder
        self._validator = validator
        self._resolver = resolver

    def get_graph_builder(self) -> DependencyGraphBuilder:
        return self._graph_builder

    def get_validator(self) -> DependencyValidator:
        return self._validator

    def get_resolver(self) -> ExecutionOrderResolver:
        return self._resolver

    def describe_capabilities(self) -> List[str]:
        return ["graph_building", "cycle_detection", "topological_sort",
                "level_grouping", "missing_dep_check"]

    def count_graph_capabilities(self) -> int:
        return 5

    def get_max_depth(self, graph: DependencyGraph) -> int:
        return graph.levels

    def count_dependencies(self, graph: DependencyGraph) -> int:
        return graph.edges


class DashboardDependencies:
    """Dashboard bridge untuk execution dependencies — 5 cards."""

    def __init__(self, graph_builder: DependencyGraphBuilder,
                 validator: DependencyValidator,
                 resolver: ExecutionOrderResolver) -> None:
        self._graph_builder = graph_builder
        self._validator = validator
        self._resolver = resolver

    def graph_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Dependency Graph",
            description="Grafik dependensi antar kandidat",
            status="ready",
            metrics={"builder_ready": True},
            items=["graph"],
        )

    def validation_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Dependency Validation",
            description="Validasi dependensi",
            status="ready",
            metrics={"cycle_detection": True},
            items=["validation"],
        )

    def order_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Execution Order",
            description="Urutan eksekusi hasil topological sort",
            status="ready",
            metrics={"resolver_ready": True},
            items=["order"],
        )

    def summary_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Dependency Summary",
            description="Ringkasan analisis dependensi",
            status="ready",
            metrics={"capabilities": 5},
            items=["summary"],
        )

    def status_card(self):
        from sam.execution.runtime.dashboard_execution import ExecutionCard
        return ExecutionCard(
            title="Dependency Status",
            description="Status dependency resolver",
            status="active",
            metrics={"graph_builder": True, "validator": True, "resolver": True},
            items=["status"],
        )
