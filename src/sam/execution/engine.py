"""
Execution Graph Engine — executes ExecutionGraph instances.

The engine is responsible for:
- Running nodes in topological order with parallel fan-out
- Applying retry policies (linear/exponential backoff + jitter)
- Applying compensation policies on failure
- Pause/resume with graph-level checkpointing
- Publishing events (graph started, node started/completed/failed, graph completed)
- Registering graphs as RuntimeResource in ResourceDirectory
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

import structlog

from .graph import ExecutionGraph, GraphStatus
from .node import (
    ExecutionNode,
    NodeStatus,
    CompensationOnFailure,
)
from .decision import DecisionNode

from sam.core.clock import TimeProvider, SystemClock
from sam.reasoning.revision import RevisionManager, RevisionTrigger
from sam.core.event_bus import EventBus
from sam.core.events import Event
from sam.core.resource_directory import ResourceDirectory
from sam.core.resource import RuntimeResource, ResourceType, ResourceStatus, ResourceOwner


# ── Result DTOs ──────────────────────────────────────────────────────


@dataclass
class NodeResult:
    """Result of executing a single node."""

    node_id: str
    status: NodeStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    attempts: int = 0
    duration_ms: float = 0.0


@dataclass
class GraphResult:
    """Result of executing an entire graph."""

    graph_id: str
    status: GraphStatus
    node_results: List[NodeResult] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0


# ── Event types ──────────────────────────────────────────────────────

EXECUTION_GRAPH_STARTED = "execution.graph.started"
EXECUTION_GRAPH_COMPLETED = "execution.graph.completed"
EXECUTION_GRAPH_FAILED = "execution.graph.failed"
EXECUTION_GRAPH_PAUSED = "execution.graph.paused"
EXECUTION_GRAPH_RESUMED = "execution.graph.resumed"
EXECUTION_GRAPH_COMPENSATED = "execution.graph.compensated"
EXECUTION_NODE_STARTED = "execution.node.started"
EXECUTION_NODE_COMPLETED = "execution.node.completed"
EXECUTION_NODE_FAILED = "execution.node.failed"
EXECUTION_NODE_COMPENSATED = "execution.node.compensated"
EXECUTION_NODE_SKIPPED = "execution.node.skipped"


# ── Engine ───────────────────────────────────────────────────────────


class ExecutionGraphEngine:
    """Executes an ExecutionGraph respecting dependencies and policies.

    Responsibilities:
    - Topological execution: nodes run only after all dependencies complete
    - Parallel fan-out: ready nodes execute concurrently via asyncio.gather
    - Retry: applies RetryPolicy with backoff + jitter
    - Compensation: runs compensation nodes on failure
    - Pause/Resume: graph-level checkpointing
    - Events: publishes lifecycle events to EventBus
    - Resource: registers graph as RuntimeResource in ResourceDirectory
    """

    def __init__(
        self,
        runtime: Any = None,  # CapabilityRuntime
        event_bus: Optional[EventBus] = None,
        clock: Optional[TimeProvider] = None,
        resource_directory: Optional[ResourceDirectory] = None,
        revision_manager: Optional[RevisionManager] = None,
    ) -> None:
        self.runtime = runtime
        self.event_bus = event_bus or EventBus()
        self.clock = clock or SystemClock()
        self.resource_directory = resource_directory or None
        self.revision_manager = revision_manager
        self._logger = structlog.get_logger().bind(component="ExecutionGraphEngine")

        # Internal state for pause/resume
        self._paused_graphs: Set[str] = set()
        self._active_graphs: Dict[str, ExecutionGraph] = {}

    # ── Public API ────────────────────────────────────────────────

    async def execute(
        self,
        graph: ExecutionGraph,
        capability_executor: Optional[Callable[[ExecutionNode], Any]] = None,
    ) -> GraphResult:
        """Execute an entire execution graph.

        Args:
            graph: The execution graph to run.
            capability_executor: Optional callable (node) → result.
                                 If not provided, uses self.runtime.execute_capability.

        Returns:
            GraphResult with final status and individual node results.
        """
        # Validate
        errors = graph.validate()
        if errors:
            self._logger.error("graph_validation_failed", graph_id=graph.id, errors=errors)
            return GraphResult(
                graph_id=graph.id,
                status=GraphStatus.FAILED,
                node_results=[],
                started_at=self.clock.now(),
                completed_at=self.clock.now(),
            )

        started_at = self.clock.now()
        self._logger.info("execution_starting", graph_id=graph.id, name=graph.name)

        # Mark graph as RUNNING
        graph.status = GraphStatus.RUNNING
        self._active_graphs[graph.id] = graph

        # Publish graph started event
        await self._publish(EXECUTION_GRAPH_STARTED, graph_id=graph.id, name=graph.name)

        # Register graph as runtime resource
        await self._register_graph_resource(graph)

        try:
            node_results = await self._run_topological(graph, capability_executor)

            # Determine final graph status from node results
            final_status = self._derive_graph_status(node_results)
            graph.status = final_status

            completed_at = self.clock.now()
            duration_ms = (completed_at - started_at).total_seconds() * 1000

            # Publish completion event
            event_type = (
                EXECUTION_GRAPH_COMPLETED if final_status == GraphStatus.COMPLETED
                else EXECUTION_GRAPH_COMPENSATED if final_status == GraphStatus.COMPENSATED
                else EXECUTION_GRAPH_FAILED
            )
            await self._publish(
                event_type,
                graph_id=graph.id,
                status=final_status.value,
                node_count=len(node_results),
            )

            # Update resource
            await self._update_graph_resource(graph, final_status)

            self._logger.info(
                "execution_finished",
                graph_id=graph.id,
                status=final_status.value,
                duration_ms=duration_ms,
            )

            return GraphResult(
                graph_id=graph.id,
                status=final_status,
                node_results=node_results,
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=duration_ms,
            )

        finally:
            self._active_graphs.pop(graph.id, None)

    async def pause(self, graph_id: str) -> None:
        """Pause a running graph at the next safe point."""
        if graph_id not in self._active_graphs:
            self._logger.warning("pause_unknown_graph", graph_id=graph_id)
            return

        self._paused_graphs.add(graph_id)
        graph = self._active_graphs[graph_id]
        graph.status = GraphStatus.PAUSED
        self._logger.info("graph_paused", graph_id=graph_id)
        await self._publish(EXECUTION_GRAPH_PAUSED, graph_id=graph_id)
        await self._update_graph_resource(graph, GraphStatus.PAUSED)

    async def resume(self, graph_id: str) -> None:
        """Resume a paused graph."""
        if graph_id not in self._paused_graphs:
            self._logger.warning("resume_unknown_or_not_paused", graph_id=graph_id)
            return

        self._paused_graphs.discard(graph_id)
        if graph_id not in self._active_graphs:
            self._logger.warning("resume_graph_not_active", graph_id=graph_id)
            return

        graph = self._active_graphs[graph_id]
        graph.status = GraphStatus.RUNNING
        self._logger.info("graph_resumed", graph_id=graph_id)
        await self._publish(EXECUTION_GRAPH_RESUMED, graph_id=graph_id)
        await self._update_graph_resource(graph, GraphStatus.RUNNING)

    async def get_status(self, graph_id: str) -> Optional[GraphStatus]:
        """Get the current status of a graph."""
        graph = self._active_graphs.get(graph_id)
        if graph:
            return graph.status
        return None

    def is_paused(self, graph_id: str) -> bool:
        """Check if a graph is currently paused."""
        return graph_id in self._paused_graphs

    # ── Internal: Execution ───────────────────────────────────────

    async def _run_topological(
        self,
        graph: ExecutionGraph,
        capability_executor: Optional[Callable[[ExecutionNode], Any]] = None,
    ) -> List[NodeResult]:
        """Run nodes in topological order with parallel fan-out.

        Strategy:
        - Maintain a set of completed nodes.
        - Each cycle: find all nodes whose dependencies are all completed.
        - Run them in parallel via asyncio.gather.
        - Repeat until all nodes are in a terminal state.
        - Decision nodes evaluate conditions and dynamically resolve next targets.
        """
        results: Dict[str, NodeResult] = {}
        pending: Set[str] = {n.id for n in graph.nodes}
        node_map = graph.node_map
        evidence: Dict[str, Any] = {}  # Accumulated evidence for decision nodes

        # Precompute mapping: branch target node -> decision execution node id
        branch_to_decision_exec: Dict[str, str] = {}
        for exec_node in graph.nodes:
            if exec_node.is_decision and exec_node.decision_id:
                decision = graph.decision_nodes.get(exec_node.decision_id)
                if decision:
                    for t in decision.branch_targets.values():
                        branch_to_decision_exec[t] = exec_node.id
                    if decision.default_target:
                        branch_to_decision_exec[decision.default_target] = exec_node.id

        # Inject implicit dependencies: ensure branch target nodes depend on their decision exec node
        for exec_node in graph.nodes:
            if exec_node.is_decision and exec_node.decision_id:
                decision = graph.decision_nodes.get(exec_node.decision_id)
                if not decision:
                    continue
                for target in set(decision.branch_targets.values()) | ({decision.default_target} if decision.default_target else set()):
                    if not target:
                        continue
                    target_node = graph.get_node(target)
                    if target_node and exec_node.id not in target_node.dependencies:
                        # mutate a copy of dependencies to avoid pydantic list immutability surprises
                        deps = list(target_node.dependencies)
                        deps.append(exec_node.id)
                        target_node.dependencies = deps
                        self._logger.debug(
                            "decision.inject_dependency",
                            decision_exec=exec_node.id,
                            target=target,
                        )

        while pending:
            # Check for pause
            if graph.id in self._paused_graphs:
                await self.clock.sleep(0.1)
                continue

            # Find ready nodes: all deps completed (allow terminal states)
            ready: List[ExecutionNode] = []
            for nid in sorted(pending):
                node = node_map[nid]
                # If this node is a branch target, delay until its decision exec node has completed
                if nid in branch_to_decision_exec:
                    decision_exec_id = branch_to_decision_exec[nid]
                    if decision_exec_id not in results or results[decision_exec_id].status not in (
                        NodeStatus.COMPLETED, NodeStatus.SKIPPED, NodeStatus.FAILED, NodeStatus.COMPENSATED
                    ):
                        continue

                deps_done = all(
                    dep in results and results[dep].status in (
                        NodeStatus.COMPLETED, NodeStatus.SKIPPED, NodeStatus.FAILED, NodeStatus.COMPENSATED
                    )
                    for dep in node.dependencies
                )
                if deps_done and node.status in (NodeStatus.PENDING,):
                    ready.append(node)

            if not ready:
                stuck = pending - {nid for nid, r in results.items() if r.status in (
                    NodeStatus.COMPLETED, NodeStatus.SKIPPED, NodeStatus.FAILED,
                    NodeStatus.COMPENSATED,
                )}
                if stuck:
                    for sid in sorted(stuck):
                        n = node_map[sid]
                        self._logger.warning("node_stuck", node_id=sid)
                        results[sid] = NodeResult(
                            node_id=sid,
                            status=NodeStatus.FAILED,
                            error="Deadlocked: dependencies never completed",
                        )
                break

            # Execute ready nodes in parallel
            tasks = [
                self._execute_with_retry(node, capability_executor, evidence)
                for node in ready
            ]
            batch_results: List[NodeResult] = await asyncio.gather(*tasks)

            for result in batch_results:
                results[result.node_id] = result
                node_map[result.node_id].status = result.status

                # Accumulate evidence from completed nodes as nested dicts
                evidence.setdefault("node", {}).setdefault(result.node_id, {})["status"] = result.status.value
                if result.output is not None:
                    evidence.setdefault("node", {}).setdefault(result.node_id, {})["output"] = result.output

            pending -= {r.node_id for r in batch_results}

            # Handle decision nodes and ABORT propagation
            for result in batch_results:
                node = node_map[result.node_id]

                # If this is a decision node, evaluate and resolve branch
                if node.is_decision and result.status in (
                    NodeStatus.COMPLETED, NodeStatus.SKIPPED
                ):
                    try:
                        target_id = graph.get_branch_target(node.id, evidence)
                    except (ValueError, KeyError) as exc:
                        self._logger.error(
                            "decision_evaluation_failed",
                            node_id=node.id,
                            error=str(exc),
                        )
                        continue

                    if target_id is not None:
                        # Ensure target node dependency on this decision node
                        if target_id in pending:
                            target_node = node_map[target_id]
                            if node.id not in target_node.dependencies:
                                target_node.dependencies = list(target_node.dependencies) + [node.id]
                                self._logger.debug(
                                    "decision.dynamic_dependency",
                                    from_node=node.id,
                                    to_node=target_id,
                                )

                        # Skip all other branch targets (they should not run)
                        decision = graph.decision_nodes.get(node.decision_id)
                        if decision:
                            branch_ids = set(decision.branch_targets.values())
                            # also include default_target as a possible branch
                            if decision.default_target:
                                branch_ids.add(decision.default_target)

                            for bid in branch_ids:
                                if bid != target_id and bid in pending:
                                    self._logger.info(
                                        "decision.skip_branch",
                                        decision_id=node.decision_id,
                                        skipped_node=bid,
                                        selected=target_id,
                                    )
                                    node_map[bid].status = NodeStatus.SKIPPED
                                    results[bid] = NodeResult(
                                        node_id=bid,
                                        status=NodeStatus.SKIPPED,
                                        error="Skipped by decision branch",
                                    )
                                    pending.discard(bid)

                    else:
                        # No target found — skip all branch targets
                        decision = graph.decision_nodes.get(node.decision_id)
                        if decision:
                            branch_ids = set(decision.branch_targets.values())
                            if decision.default_target:
                                branch_ids.add(decision.default_target)
                            for bid in branch_ids:
                                if bid in pending:
                                    node_map[bid].status = NodeStatus.SKIPPED
                                    results[bid] = NodeResult(
                                        node_id=bid,
                                        status=NodeStatus.SKIPPED,
                                        error="Skipped by decision (no matching condition and no default)",
                                    )
                                    pending.discard(bid)

                    self._logger.info(
                        "decision.branch",
                        node_id=node.id,
                        target=target_id,
                        evidence_keys=list(evidence.keys()),
                    )

                # Check for revision trigger based on decision evidence
                await self._check_and_propose_revision(
                    node, result, evidence, graph,
                )

                # ABORT propagation on failure
                if result.status == NodeStatus.FAILED:
                    if node.compensation_policy.on_failure == CompensationOnFailure.ABORT:
                        self._logger.info(
                            "aborting_graph_on_node_failure",
                            node_id=result.node_id,
                            graph_id=graph.id,
                        )
                        for nid in sorted(pending):
                            node_map[nid].status = NodeStatus.SKIPPED
                            results[nid] = NodeResult(
                                node_id=nid, status=NodeStatus.SKIPPED,
                                error="Graph aborted due to upstream failure",
                            )
                        pending.clear()

        return [results[n.id] for n in graph.nodes if n.id in results]

    async def _execute_with_retry(
        self,
        node: ExecutionNode,
        capability_executor: Optional[Callable[[ExecutionNode], Any]] = None,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> NodeResult:
        """Execute a single node with retry and compensation logic.

        Decision nodes (is_decision=True) are treated as lightweight:
        they just record a COMPLETED status rather than invoking a capability.
        """
        # Decision nodes: skip capability invocation; mark as COMPLETED
        if node.is_decision:
            return await self._execute_decision_node(node, evidence or {})
        started_at = self.clock.now()
        attempts = 0
        last_error: Optional[Exception] = None

        # Mark as RUNNING and publish
        node.status = NodeStatus.RUNNING
        node.started_at = started_at
        await self._publish(EXECUTION_NODE_STARTED, node_id=node.id, graph_id=node.graph_id)

        while attempts < node.retry_policy.max_attempts:
            attempts += 1
            try:
                output = await self._invoke_capability(node, capability_executor)
                # Success
                completed_at = self.clock.now()
                duration_ms = (completed_at - started_at).total_seconds() * 1000

                node.status = NodeStatus.COMPLETED
                node.completed_at = completed_at
                node.outputs = output if isinstance(output, dict) else {"_result": output}

                result = NodeResult(
                    node_id=node.id,
                    status=NodeStatus.COMPLETED,
                    output=node.outputs,
                    attempts=attempts,
                    duration_ms=duration_ms,
                )
                await self._publish(
                    EXECUTION_NODE_COMPLETED,
                    node_id=node.id,
                    graph_id=node.graph_id,
                    attempts=attempts,
                    duration_ms=duration_ms,
                )
                return result

            except Exception as exc:
                last_error = exc
                self._logger.warning(
                    "node_execution_failed",
                    node_id=node.id,
                    attempt=attempts,
                    max_attempts=node.retry_policy.max_attempts,
                    error=str(exc),
                )

                # Check: is this the last attempt?
                if attempts >= node.retry_policy.max_attempts:
                    break

                # Apply retry delay (backoff + jitter)
                delay = node.retry_policy.delay_for_attempt(attempts)
                self._logger.debug(
                    "retry_delay",
                    node_id=node.id,
                    attempt=attempts,
                    delay_seconds=delay,
                )

                # Publish retry event
                await self._publish(
                    EXECUTION_NODE_FAILED,
                    node_id=node.id,
                    graph_id=node.graph_id,
                    attempt=attempts,
                    error=str(exc),
                    will_retry=True,
                )

                await self.clock.sleep(delay)

        # All retries exhausted — apply compensation
        return await self._handle_node_failure(
            node, last_error or RuntimeError("unknown"),
            attempts, started_at, capability_executor,
        )

    async def _execute_decision_node(
        self,
        node: ExecutionNode,
        evidence: Dict[str, Any],
    ) -> NodeResult:
        """Execute a decision node: evaluate conditions and resolve branch.

        Decision nodes don't invoke capabilities; they evaluate evidence
        and determine the next target node. The topological loop uses
        get_branch_target() to resolve the actual path.
        """
        started_at = self.clock.now()
        node.status = NodeStatus.RUNNING
        node.started_at = started_at

        await self._publish(EXECUTION_NODE_STARTED, node_id=node.id, graph_id=node.graph_id)

        # Lightweight: just mark COMPLETED after collecting outcome
        completed_at = self.clock.now()
        duration_ms = (completed_at - started_at).total_seconds() * 1000

        node.status = NodeStatus.COMPLETED
        node.completed_at = completed_at

        outcome = f"decision: {node.id}"
        node.outputs = {
            "decision_id": node.decision_id,
            "decision_outcome": outcome,
        }

        result = NodeResult(
            node_id=node.id,
            status=NodeStatus.COMPLETED,
            output=node.outputs,
            attempts=0,
            duration_ms=duration_ms,
        )

        await self._publish(
            EXECUTION_NODE_COMPLETED,
            node_id=node.id,
            graph_id=node.graph_id,
            is_decision=True,
        )

        return result

    async def _handle_node_failure(
        self,
        node: ExecutionNode,
        error: Exception,
        attempts: int,
        started_at: datetime,
        capability_executor: Optional[Callable[[ExecutionNode], Any]] = None,
    ) -> NodeResult:
        """Handle a node that exhausted all retries."""
        completed_at = self.clock.now()
        duration_ms = (completed_at - started_at).total_seconds() * 1000
        error_msg = str(error)

        on_failure = node.compensation_policy.on_failure

        self._logger.warning(
            "node_final_failure",
            node_id=node.id,
            on_failure=on_failure.value,
            error=error_msg,
        )

        if on_failure == CompensationOnFailure.COMPENSATE:
            # Run compensation node if specified
            comp_node_id = node.compensation_policy.compensation_node_id
            if comp_node_id:
                comp_result = await self._run_compensation(
                    node.graph_id, comp_node_id, error_msg, capability_executor,
                )
                if comp_result.status == NodeStatus.COMPLETED:
                    node.status = NodeStatus.COMPENSATED
                    node.completed_at = completed_at
                    result = NodeResult(
                        node_id=node.id,
                        status=NodeStatus.COMPENSATED,
                        error=error_msg,
                        attempts=attempts,
                        duration_ms=duration_ms,
                    )
                    await self._publish(
                        EXECUTION_NODE_COMPENSATED,
                        node_id=node.id,
                        graph_id=node.graph_id,
                        compensation_node=comp_node_id,
                    )
                    return result

            # Compensation failed or not specified — mark as failed
            node.status = NodeStatus.FAILED
            node.completed_at = completed_at
            result = NodeResult(
                node_id=node.id,
                status=NodeStatus.FAILED,
                error=error_msg,
                attempts=attempts,
                duration_ms=duration_ms,
            )
            await self._publish(
                EXECUTION_NODE_FAILED,
                node_id=node.id,
                graph_id=node.graph_id,
                attempt=attempts,
                error=error_msg,
                will_retry=False,
            )
            return result

        elif on_failure == CompensationOnFailure.RETRY:
            # ESCALATE/RETRY: mark FAILED — retry is exhausted above
            # (RETRY means the node *does* retry up to max_attempts;
            #  after exhaustion, still mark as FAILED)
            node.status = NodeStatus.FAILED
            node.completed_at = completed_at
            result = NodeResult(
                node_id=node.id,
                status=NodeStatus.FAILED,
                error=error_msg,
                attempts=attempts,
                duration_ms=duration_ms,
            )
            await self._publish(
                EXECUTION_NODE_FAILED,
                node_id=node.id,
                graph_id=node.graph_id,
                attempt=attempts,
                error=error_msg,
                will_retry=False,
            )
            return result

        else:
            # ABORT or ESCALATE
            node.status = NodeStatus.FAILED
            node.completed_at = completed_at
            result = NodeResult(
                node_id=node.id,
                status=NodeStatus.FAILED,
                error=error_msg,
                attempts=attempts,
                duration_ms=duration_ms,
            )
            await self._publish(
                EXECUTION_NODE_FAILED,
                node_id=node.id,
                graph_id=node.graph_id,
                attempt=attempts,
                error=error_msg,
                will_retry=False,
            )
            return result

    async def _run_compensation(
        self,
        graph_id: str,
        compensation_node_id: str,
        original_error: str,
        capability_executor: Optional[Callable[[ExecutionNode], Any]] = None,
    ) -> NodeResult:
        """Run a compensation node.

        This looks for the compensation node in the active graph. If not
        found as a regular node, it executes the capability standalone.
        """
        graph = self._active_graphs.get(graph_id)
        comp_node: Optional[ExecutionNode] = None

        if graph:
            comp_node = graph.get_node(compensation_node_id)

        node_id = compensation_node_id
        started = self.clock.now()

        try:
            if comp_node:
                comp_node.status = NodeStatus.RUNNING
                comp_node.started_at = started
                await self._publish(
                    EXECUTION_NODE_STARTED,
                    node_id=node_id,
                    graph_id=graph_id,
                    is_compensation=True,
                )
                output = await self._invoke_capability(comp_node, capability_executor)
                comp_node.status = NodeStatus.COMPLETED
                comp_node.completed_at = self.clock.now()
                comp_node.outputs = output if isinstance(output, dict) else {"_result": output}
            else:
                # Execute directly via runtime if node not in graph
                await self._publish(
                    EXECUTION_NODE_STARTED,
                    node_id=node_id,
                    graph_id=graph_id,
                    is_compensation=True,
                )
                # We can't invoke a node that isn't in the graph — treat as skipped
                self._logger.warning(
                    "compensation_node_not_found",
                    node_id=node_id,
                    graph_id=graph_id,
                )
                return NodeResult(
                    node_id=node_id,
                    status=NodeStatus.FAILED,
                    error=f"Compensation node '{node_id}' not found in graph",
                )

        except Exception as exc:
            self._logger.error(
                "compensation_failed",
                node_id=node_id,
                error=str(exc),
            )
            return NodeResult(
                node_id=node_id,
                status=NodeStatus.FAILED,
                error=f"Compensation failed: {exc}",
            )

        elapsed = (self.clock.now() - started).total_seconds() * 1000
        result = NodeResult(
            node_id=node_id,
            status=NodeStatus.COMPLETED,
            output=comp_node.outputs if comp_node else None,
            duration_ms=elapsed,
        )
        await self._publish(
            EXECUTION_NODE_COMPLETED,
            node_id=node_id,
            graph_id=graph_id,
            is_compensation=True,
        )
        return result

    async def _invoke_capability(
        self,
        node: ExecutionNode,
        capability_executor: Optional[Callable[[ExecutionNode], Any]] = None,
    ) -> Any:
        """Invoke a capability for a node.

        Precedence:
        1. Explicit capability_executor callable (test hook)
        2. self.runtime.execute_capability (CapabilityRuntime)
        """
        if capability_executor is not None:
            result = capability_executor(node)
            if asyncio.iscoroutine(result):
                return await result
            return result

        if self.runtime is not None:
            # Create an ExecutionContext for the capability
            from sam.runtime.context import ExecutionContext

            ctx = ExecutionContext(
                execution_id=uuid.UUID(node.graph_id),
                workflow_id=node.graph_id,
                step_name=node.id,
                inputs=node.inputs,
            )
            return await self.runtime.execute_capability(node.capability_id, ctx)

        raise RuntimeError(
            f"No capability executor available for node '{node.id}'. "
            f"Provide a CapabilityRuntime or capability_executor callable."
        )

    # ── Internal: Graph Status ────────────────────────────────────

    def _derive_graph_status(self, results: List[NodeResult]) -> GraphStatus:
        """Derive final graph status from node results."""
        statuses = {r.status for r in results}

        if not results:
            return GraphStatus.FAILED  # empty graph with no results

        if all(s in (NodeStatus.COMPLETED, NodeStatus.SKIPPED) for s in statuses):
            return GraphStatus.COMPLETED

        if NodeStatus.COMPENSATED in statuses:
            return GraphStatus.COMPENSATED

        return GraphStatus.FAILED

    # ── Internal: Events ──────────────────────────────────────────

    async def _publish(self, event_type: str, **payload: Any) -> None:
        """Publish an execution event."""
        event = Event(
            id=str(uuid.uuid4()),
            type=event_type,
            source="execution_graph_engine",
            payload=payload,
            timestamp=self.clock.now(),
        )
        try:
            await self.event_bus.publish(event)
        except Exception:
            self._logger.debug(
                "event_publish_failed",
                event_type=event_type,
            )

    # ── Internal: Revision Integration ────────────────────────────

    async def _check_and_propose_revision(
        self,
        node: ExecutionNode,
        result: NodeResult,
        evidence: Dict[str, Any],
        graph: ExecutionGraph,
    ) -> Optional[Any]:
        """Check if a completed node triggers a graph revision.

        Called after each node completes. If the node is a decision node
        and its evidence suggests a significant change, a revision is
        proposed via RevisionManager.

        Returns:
            Optional GraphRevision if proposed, None otherwise.
        """
        if not self.revision_manager:
            return None

        # Only trigger revisions for decision nodes with evidence
        if not node.is_decision:
            return None

        # Check decision evidence: did we branch away from the "happy path"?
        # Heuristic: look for node evidence that indicates failure or warning
        ev = evidence.get("node", {})
        node_ev = ev.get(node.id, {})
        decision_outcome = node_ev.get("output", {}).get("decision_outcome", "")

        # Inspect all accumulated evidence for significant signals
        trigger_reasons = []
        for nid, ned in ev.items():
            if nid == node.id:
                continue
            status = ned.get("status", "")
            if status in ("FAILED", "COMPENSATED"):
                trigger_reasons.append(f"Node {nid} is {status}")
            output = ned.get("output", {})
            if output and isinstance(output, dict):
                for key, val in output.items():
                    if isinstance(val, str) and "unhealthy" in val.lower():
                        trigger_reasons.append(f"{nid}.{key}: {val}")
                    elif isinstance(val, str) and "warning" in val.lower():
                        trigger_reasons.append(f"{nid}.{key}: {val}")

        if not trigger_reasons:
            return None

        reason = "; ".join(trigger_reasons)
        self._logger.info(
            "revision.trigger_detected",
            graph_id=graph.id,
            node_id=node.id,
            reason=reason,
        )

        # Propose revision
        revision = await self.revision_manager.propose_revision(
            graph_id=graph.id,
            reason=reason,
            changes={
                "new_nodes": [],
                "modified_nodes": [],
                "removed_nodes": [],
            },
            trigger=RevisionTrigger.DECISION_NODE,
            current_graph=graph,
        )

        self._logger.info(
            "revision.proposed_for_graph",
            graph_id=graph.id,
            revision_id=revision.id,
            version=revision.version,
        )

        return revision

    # ── Internal: Resource Integration ────────────────────────────

    async def _register_graph_resource(self, graph: ExecutionGraph) -> None:
        """Register the graph as a RuntimeResource in ResourceDirectory."""
        if self.resource_directory is None:
            return

        resource = RuntimeResource(
            id=f"execution:graph:{graph.id}",
            type=ResourceType.CUSTOM,  # generic type
            status=ResourceStatus.ACTIVE,
            owner=ResourceOwner(type="execution_engine", id=graph.id),
            data={
                "graph_id": graph.id,
                "name": graph.name,
                "status": graph.status.value,
                "correlation_id": graph.correlation_id,
                "node_count": len(graph.nodes),
            },
        )
        try:
            await self.resource_directory.register(resource)
        except Exception as exc:
            self._logger.debug(
                "graph_resource_register_failed",
                graph_id=graph.id,
                error=str(exc),
            )

    async def _update_graph_resource(
        self, graph: ExecutionGraph, status: GraphStatus
    ) -> None:
        """Update the graph's resource status."""
        if self.resource_directory is None:
            return

        resource_id = f"execution:graph:{graph.id}"
        try:
            await self.resource_directory.update_status(resource_id, ResourceStatus.ACTIVE)
            # Also update data
            await self.resource_directory.set_data(resource_id, {
                "graph_id": graph.id,
                "name": graph.name,
                "status": status.value,
                "correlation_id": graph.correlation_id,
                "node_count": len(graph.nodes),
                "paused": graph.id in self._paused_graphs,
            })
        except Exception as exc:
            self._logger.debug(
                "graph_resource_update_failed",
                graph_id=graph.id,
                error=str(exc),
            )
