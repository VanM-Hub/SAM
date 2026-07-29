# OP-394 — Execution Planner
# Python 3.8 compatible, frozen dataclass, synchronous only
# Plans execution by ordering dependencies, grouping parallel tasks, aggregating risk
# No execution, no side effects

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid

from .execution_request import (
    ExecutionRequest,
    ExecutionPlan,
    ExecutionTarget,
    ExecutionParameter,
    ExecutionStatus,
    ExecutionRisk,
)


# ---------------------------------------------------------------------------
# Planner DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DependencyEdge:
    """A dependency between two requests."""
    from_request_id: str = ""
    to_request_id: str = ""
    dependency_type: str = "requires"  # requires, blocks, triggers


# ---------------------------------------------------------------------------
# ExecutionPlanner
# ---------------------------------------------------------------------------

class ExecutionPlanner:
    """Plans execution by analyzing requests, dependencies, and risk.

    Input: MissionProposal, GuardianDecision, ExecutionRequest objects
    Output: ExecutionPlan (immutable DTO)

    No execution — pure analysis and ordering.
    """

    def __init__(self) -> None:
        self._dependencies: List[DependencyEdge] = []

    # --- Dependency Management ---

    def add_dependency(
        self,
        from_request_id: str,
        to_request_id: str,
        dependency_type: str = "requires",
    ) -> None:
        """Add a dependency edge between two requests."""
        self._dependencies.append(DependencyEdge(
            from_request_id=from_request_id,
            to_request_id=to_request_id,
            dependency_type=dependency_type,
        ))

    def clear_dependencies(self) -> None:
        self._dependencies.clear()

    def get_dependencies(self) -> Tuple[DependencyEdge, ...]:
        return tuple(self._dependencies)

    # --- Risk Aggregation ---

    @staticmethod
    def aggregate_risk(requests: Tuple[ExecutionRequest, ...]) -> ExecutionRisk:
        """Aggregate risk across multiple requests."""
        if not requests:
            return ExecutionRisk()

        levels = {
            "low": 0,
            "medium": 1,
            "high": 2,
            "critical": 3,
        }
        reverse_levels = {v: k for k, v in levels.items()}

        max_level = 0
        total_score = 0.0
        all_factors: List[str] = []
        requires_guardian = False

        for req in requests:
            level_val = levels.get(req.risk.level, 0)
            max_level = max(max_level, level_val)
            total_score += req.risk.score
            all_factors.extend(req.risk.factors)
            if req.risk.requires_guardian or req.requires_guardian:
                requires_guardian = True

        avg_score = total_score / len(requests) if requests else 0.0

        return ExecutionRisk(
            level=reverse_levels.get(max_level, "low"),
            score=round(avg_score, 4),
            factors=tuple(dict.fromkeys(all_factors)),  # unique, preserve order
            requires_approval=max_level >= 1 or any(r.requires_human_approval for r in requests),
            requires_guardian=requires_guardian,
            description=f"Aggregated risk from {len(requests)} requests",
        )

    # --- Dependency Ordering ---

    def _compute_dependency_order(
        self,
        requests: Tuple[ExecutionRequest, ...],
    ) -> Tuple[str, ...]:
        """Compute topological order of request IDs based on dependencies.

        Simple Kahn's algorithm for DAG ordering.
        """
        req_ids = [r.request_id for r in requests]
        id_set = set(req_ids)

        # Build adjacency and in-degree
        adj: Dict[str, List[str]] = {rid: [] for rid in req_ids}
        in_degree: Dict[str, int] = {rid: 0 for rid in req_ids}

        for dep in self._dependencies:
            if dep.from_request_id in id_set and dep.to_request_id in id_set:
                if dep.dependency_type == "requires":
                    adj[dep.from_request_id].append(dep.to_request_id)
                    in_degree[dep.to_request_id] = in_degree.get(dep.to_request_id, 0) + 1

        # Kahn's algorithm
        queue = [rid for rid in req_ids if in_degree.get(rid, 0) == 0]
        order = []

        while queue:
            node = queue.pop(0)
            order.append(node)
            for neighbor in adj.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If cycle detected (incomplete ordering), append remaining
        remaining = [rid for rid in req_ids if rid not in order]
        order.extend(remaining)

        return tuple(order)

    def _compute_parallel_groups(
        self,
        requests: Tuple[ExecutionRequest, ...],
        dependency_order: Tuple[str, ...],
    ) -> Tuple[Tuple[str, ...], ...]:
        """Group requests that can run in parallel (no dependencies between them).

        Simple heuristic: requests with same dependency depth.
        """
        depth: Dict[str, int] = {}
        for rid in dependency_order:
            deps = [
                d for d in self._dependencies
                if d.to_request_id == rid and d.from_request_id in dependency_order
            ]
            if deps:
                depth[rid] = max(depth.get(d.from_request_id, 0) for d in deps) + 1
            else:
                depth[rid] = 0

        # Group by depth
        by_depth: Dict[int, List[str]] = {}
        for rid, d in depth.items():
            by_depth.setdefault(d, []).append(rid)

        return tuple(tuple(v) for v in by_depth.values())

    # --- Rollback Requirement ---

    @staticmethod
    def _compute_rollback_requirement(
        requests: Tuple[ExecutionRequest, ...],
    ) -> bool:
        """Determine if rollback is needed based on risk levels."""
        return any(r.risk.level in ("high", "critical") for r in requests)

    # --- Main Planning ---

    def plan(
        self,
        requests: Tuple[ExecutionRequest, ...],
        description: str = "",
    ) -> ExecutionPlan:
        """Create an execution plan from a set of requests.

        Automatically orders by dependencies, groups parallels,
        computes aggregated risk, and determines rollback requirement.
        """
        if not requests:
            return ExecutionPlan(description=description or "Empty plan")

        # Mark all as planned
        planned_requests = tuple(
            r.with_status(ExecutionStatus.planned()) for r in requests
        )

        # Compute ordering
        dependency_order = self._compute_dependency_order(planned_requests)

        # Compute parallel groups
        parallel_groups = self._compute_parallel_groups(planned_requests, dependency_order)

        # Compute aggregated risk
        aggregated_risk = self.aggregate_risk(planned_requests)

        # Compute rollback requirement
        rollback_required = self._compute_rollback_requirement(planned_requests)

        # Estimate total duration (sequential sum)
        estimated_duration = 0
        for group in parallel_groups:
            # Longest in group + sequential
            max_group = max(
                (0,),
                key=lambda x: x,
                default=0,
            )
            # Simple heuristic: 1 second per request
            estimated_duration += len(group) * 1

        return ExecutionPlan(
            requests=planned_requests,
            dependency_order=dependency_order,
            parallel_groups=parallel_groups,
            rollback_required=rollback_required,
            estimated_duration_seconds=estimated_duration,
            aggregated_risk=aggregated_risk,
            description=description or f"Plan for {len(requests)} requests",
        )
