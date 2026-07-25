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
from .decision import DecisionNode


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
    decision_nodes: Dict[str, DecisionNode] = Field(
        default_factory=dict,
        description="Decision nodes keyed by decision_id",
    )
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
        - Decision nodes have valid branch_targets referencing existing nodes
        - Decision nodes are referenced by an ExecutionNode with is_decision=True
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

        # 5. Decision node validation
        for decision_id, decision_node in self.decision_nodes.items():
            # 5a. Each branch target must reference an existing node
            for cond_idx, target_id in decision_node.branch_targets.items():
                if target_id not in node_ids:
                    errors.append(
                        f"Decision node '{decision_id}' branch target '{target_id}' "
                        f"(condition {cond_idx}) not found in nodes list"
                    )

            # 5b. Default target must reference an existing node (if set)
            if decision_node.default_target is not None:
                if decision_node.default_target not in node_ids:
                    errors.append(
                        f"Decision node '{decision_id}' default target "
                        f"'{decision_node.default_target}' not found in nodes list"
                    )

            # 5c. Branch targets must exist for each condition index
            for idx in range(len(decision_node.conditions)):
                if str(idx) not in decision_node.branch_targets:
                    errors.append(
                        f"Decision node '{decision_id}' condition {idx} has no "
                        f"corresponding branch_target entry for 'str(idx)'"
                    )

            # 5d. At least one of branch_targets or default_target must be set
            if not decision_node.branch_targets and decision_node.default_target is None:
                errors.append(
                    f"Decision node '{decision_id}' has no branch_targets "
                    f"and no default_target"
                )

        # 6. is_decision nodes must have a valid decision_id
        for node in self.nodes:
            if node.is_decision:
                if not node.decision_id:
                    errors.append(
                        f"Node '{node.id}' has is_decision=True but no decision_id"
                    )
                elif node.decision_id not in self.decision_nodes:
                    errors.append(
                        f"Node '{node.id}' references unknown decision_id "
                        f"'{node.decision_id}'"
                    )

        return errors

    def get_branch_target(
        self,
        node_id: str,
        evidence: Dict[str, Any],
    ) -> Optional[str]:
        """Evaluate a decision node's conditions and return the target node ID.

        Args:
            node_id: The ExecutionNode ID (must have is_decision=True).
            evidence: Collected execution evidence dict.

        Returns:
            The target node ID from the first matching condition, default_target,
            or None if neither matches and no default is set.

        Raises:
            ValueError: If node_id is not a decision node or decision_id is invalid.
        """
        node = self.get_node(node_id)
        if node is None:
            raise ValueError(f"Node '{node_id}' not found in graph")
        if not node.is_decision:
            raise ValueError(f"Node '{node_id}' is not a decision node")

        decision_id = node.decision_id
        if not decision_id or decision_id not in self.decision_nodes:
            raise ValueError(
                f"Node '{node_id}' has invalid or missing decision_id "
                f"'{decision_id}'"
            )

        decision = self.decision_nodes[decision_id]
        return decision.evaluate(evidence)

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
