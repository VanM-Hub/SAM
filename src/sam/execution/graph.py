"""
Execution Graph models — the top-level execution unit.

An ExecutionGraph contains a set of ExecutionNodes connected by
dependency edges. The graph defines the execution topology: which
nodes are entry points, which are exits, and the dependency
relationships between them.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from .node import ExecutionNode, NodeStatus


# ── Enums ────────────────────────────────────────────────────────────


class GraphStatus(str, Enum):
    """Execution graph lifecycle states."""

    CREATED = "CREATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    COMPENSATED = "COMPENSATED"


# ── Edge ─────────────────────────────────────────────────────────────


class ExecutionEdge(BaseModel):
    """Directed edge between two execution nodes."""

    from_node: str = Field(description="Source node ID")
    to_node: str = Field(description="Target node ID (depends on from_node)")

    class Config:
        extra = "forbid"


# ── Execution Graph ──────────────────────────────────────────────────


class ExecutionGraph(BaseModel):
    """A directed execution graph containing capability invocation nodes.

    The graph specifies:
    - All nodes and their dependencies
    - Entry nodes (no upstream dependencies — start points)
    - Exit nodes (no downstream dependents — end points)

    Validation:
    - No cycles allowed in the dependency graph
    - All dependency references must point to existing nodes
    - Entry and exit nodes must exist in the nodes list
    """

    id: str = Field(description="Unique graph identifier (UUID)")
    name: str = Field(description="Human-readable graph name")
    nodes: List[ExecutionNode] = Field(default_factory=list, description="All execution nodes")
    entry_nodes: List[str] = Field(
        default_factory=list,
        description="Node IDs with no upstream dependencies",
    )
    exit_nodes: List[str] = Field(
        default_factory=list,
        description="Node IDs that are not dependencies of any other node",
    )
    status: GraphStatus = Field(default=GraphStatus.CREATED, description="Current lifecycle state")
    correlation_id: str = Field(description="Correlation ID linking this execution")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(default=None, description="When created")
    updated_at: Optional[datetime] = Field(default=None, description="When last updated")

    class Config:
        extra = "forbid"

    # ── Convenience ─────────────────────────────────────────────────

    @property
    def node_map(self) -> Dict[str, ExecutionNode]:
        """Return a dict mapping node ID → node for O(1) lookup."""
        return {n.id: n for n in self.nodes}

    def get_node(self, node_id: str) -> Optional[ExecutionNode]:
        """Get a node by ID, returning None if not found."""
        return self.node_map.get(node_id)

    # ── Dependency Analysis ─────────────────────────────────────────

    @property
    def edges(self) -> List[ExecutionEdge]:
        """Derive all edges from node dependencies in topological order."""
        result: List[ExecutionEdge] = []
        for node in self.nodes:
            for dep_id in node.dependencies:
                result.append(ExecutionEdge(from_node=dep_id, to_node=node.id))
        return result

    def downstream(self, node_id: str) -> List[str]:
        """Return node IDs that depend on the given node."""
        result: List[str] = []
        for node in self.nodes:
            if node_id in node.dependencies:
                result.append(node.id)
        return result

    def upstream(self, node_id: str) -> List[str]:
        """Return node IDs that the given node depends on."""
        node = self.get_node(node_id)
        return list(node.dependencies) if node else []

    # ── Validation ──────────────────────────────────────────────────

    def validate(self) -> List[str]:
        """Validate the graph structure. Returns list of error messages.

        Checks:
        - All dependency references exist as nodes
        - No cycles in the dependency graph
        - Entry nodes match nodes with zero dependencies
        - Exit nodes match nodes not depended upon by others
        """
        errors: List[str] = []
        node_ids = self.node_map.keys()

        # 1. All dependency references must exist
        for node in self.nodes:
            for dep_id in node.dependencies:
                if dep_id not in node_ids:
                    errors.append(
                        f"Node '{node.id}' depends on non-existent node '{dep_id}'"
                    )

        # 2. No cycles
        cycle = self._detect_cycle()
        if cycle:
            errors.append(f"Cycle detected in execution graph: {' → '.join(cycle)}")

        # 3. Entry nodes must have zero dependencies
        for entry_id in self.entry_nodes:
            node = self.get_node(entry_id)
            if node is None:
                errors.append(f"Entry node '{entry_id}' not found in nodes list")
            elif node.dependencies:
                errors.append(
                    f"Entry node '{entry_id}' has {len(node.dependencies)} dependencies"
                )

        # 4. Exit nodes must not be upstream of any other node
        for exit_id in self.exit_nodes:
            node = self.get_node(exit_id)
            if node is None:
                errors.append(f"Exit node '{exit_id}' not found in nodes list")
            else:
                downstream = self.downstream(exit_id)
                if downstream:
                    errors.append(
                        f"Exit node '{exit_id}' is a dependency of: {', '.join(downstream)}"
                    )

        return errors

    def is_valid(self) -> bool:
        """Return True if the graph passes all structural validations."""
        return len(self.validate()) == 0

    def _detect_cycle(self) -> List[str]:
        """Detect a cycle in the dependency graph using DFS colouring.

        Returns the first cycle path found, or empty list if acyclic.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: Dict[str, int] = {n.id: WHITE for n in self.nodes}
        parent: Dict[str, Optional[str]] = {}

        def _dfs(node_id: str) -> Optional[List[str]]:
            color[node_id] = GRAY
            node = self.get_node(node_id)
            if node:
                for dep_id in node.dependencies:
                    if dep_id not in color:
                        continue  # skip non-existent deps (validated elsewhere)
                    if color[dep_id] == GRAY:
                        # Found a cycle — build the path
                        path = [dep_id]
                        cursor = node_id
                        while cursor != dep_id:
                            path.append(cursor)
                            cursor = parent.get(cursor, dep_id)
                            if cursor == dep_id:
                                break
                        path.append(dep_id)
                        path.reverse()
                        return path
                    if color[dep_id] == WHITE:
                        parent[dep_id] = node_id
                        result = _dfs(dep_id)
                        if result:
                            return result
            color[node_id] = BLACK
            return None

        for nid in color:
            if color[nid] == WHITE:
                result = _dfs(nid)
                if result:
                    return result
        return []
