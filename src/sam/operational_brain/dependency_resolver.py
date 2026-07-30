"""Dependency Resolver — menyelesaikan dependensi antar goals.

Mengelola graph dependensi, deteksi cycle, dan topological sort.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple

from sam.operational_brain.operational_goal import OperationalGoal


class CycleError(Exception):
    """Raised when a cycle is detected in dependency graph."""


@dataclass(frozen=True)
class DependencyNode:
    """Immutable node dalam dependency graph."""
    goal_id: str
    title: str
    depends_on: Tuple[str, ...] = field(default_factory=tuple)  # goal_ids
    depended_by: Tuple[str, ...] = field(default_factory=tuple)  # reverse


@dataclass(frozen=True)
class DependencyGraph:
    """Immutable dependency graph dengan topological order."""
    nodes: Tuple[DependencyNode, ...] = field(default_factory=tuple)
    topological_order: Tuple[str, ...] = field(default_factory=tuple)
    has_cycles: bool = False


class DependencyResolver:
    """Menyelesaikan dependensi antar goals."""

    def __init__(self):
        self._graph: Dict[str, Set[str]] = {}  # goal_id -> set of dependencies
        self._goals: Dict[str, OperationalGoal] = {}

    def add_goal(self, goal: OperationalGoal) -> None:
        self._goals[goal.goal_id] = goal
        if goal.goal_id not in self._graph:
            self._graph[goal.goal_id] = set()
        for dep_id in goal.dependencies:
            self._graph.setdefault(dep_id, set())
            if dep_id != goal.goal_id:
                self._graph[goal.goal_id].add(dep_id)

    def remove_goal(self, goal_id: str) -> None:
        self._graph.pop(goal_id, None)
        self._goals.pop(goal_id, None)
        for deps in self._graph.values():
            deps.discard(goal_id)

    def clear(self) -> None:
        self._graph.clear()
        self._goals.clear()

    def has_dependencies(self, goal_id: str) -> bool:
        return bool(self._graph.get(goal_id, set()))

    def dependencies_of(self, goal_id: str) -> List[str]:
        return sorted(self._graph.get(goal_id, set()))

    def dependents_of(self, goal_id: str) -> List[str]:
        return sorted(g for g, deps in self._graph.items() if goal_id in deps)

    def find_cycles(self) -> List[Tuple[str, ...]]:
        """Detect all cycles. Returns list of cycles as tuple of goal_ids."""
        WHITE, GREY, BLACK = 0, 1, 2
        color: Dict[str, int] = {g: WHITE for g in self._graph}
        cycles: List[Tuple[str, ...]] = []
        path: List[str] = []

        def dfs(node: str) -> None:
            color[node] = GREY
            path.append(node)
            for neighbor in self._graph.get(node, set()):
                if neighbor not in color:
                    color[neighbor] = WHITE
                if color[neighbor] == GREY:
                    # cycle found
                    idx = path.index(neighbor)
                    cycle = tuple(path[idx:] + [neighbor])
                    cycles.append(cycle)
                elif color[neighbor] == WHITE:
                    dfs(neighbor)
            path.pop()
            color[node] = BLACK

        for node in list(self._graph):
            if color[node] == WHITE:
                dfs(node)
        return cycles

    def topological_sort(self) -> List[str]:
        """Return goal_ids in topological order (dependencies first)."""
        cycles = self.find_cycles()
        if cycles:
            raise CycleError(f"Dependency cycles detected: {cycles}")
        visited: Set[str] = set()
        result: List[str] = []
        temp_visited: Set[str] = set()

        def dfs(node: str) -> None:
            if node in temp_visited:
                return
            if node in visited:
                return
            temp_visited.add(node)
            for dep in self._graph.get(node, set()):
                if dep not in visited:
                    dfs(dep)
            temp_visited.discard(node)
            visited.add(node)
            result.append(node)

        for node in list(self._graph):
            if node not in visited:
                dfs(node)
        return result

    def build_graph(self) -> DependencyGraph:
        """Build immutable snapshot of dependency graph."""
        nodes: List[DependencyNode] = []
        for gid in self._graph:
            deps = tuple(sorted(self._graph[gid]))
            dep_by = tuple(sorted(self.dependents_of(gid)))
            title = self._goals[gid].title if gid in self._goals else "?"
            nodes.append(DependencyNode(goal_id=gid, title=title, depends_on=deps, depended_by=dep_by))
        has_cycles = bool(self.find_cycles())
        topo: List[str] = []
        if not has_cycles:
            try:
                topo = self.topological_sort()
            except CycleError:
                has_cycles = True
        return DependencyGraph(
            nodes=tuple(sorted(nodes, key=lambda n: n.goal_id)),
            topological_order=tuple(topo),
            has_cycles=has_cycles,
        )

    @property
    def goal_ids(self) -> List[str]:
        return list(self._graph.keys())
