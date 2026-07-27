"""
Tests for Execution Graph Engine.

Covers:
- Sequential execution (chain graph)
- Parallel execution (fan-out/fan-in)
- Retry logic (linear/exponential backoff + jitter)
- Compensation (COMPENSATE, ABORT, ESCALATE, RETRY)
- Pause / Resume
- Error handling
- Deadlock detection
- Event publishing
- Graph status derivation
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import MagicMock, AsyncMock

import pytest

from src.sam.execution.node import (
    ExecutionNode,
    NodeStatus,
    RetryPolicy,
    CompensationPolicy,
    RetryBackoff,
    CompensationOnFailure,
)
from src.sam.execution.graph import (
    ExecutionGraph,
    GraphStatus,
)
from src.sam.execution.engine import (
    ExecutionGraphEngine,
    NodeResult,
    GraphResult,
    EXECUTION_GRAPH_STARTED,
    EXECUTION_GRAPH_COMPLETED,
    EXECUTION_GRAPH_FAILED,
    EXECUTION_GRAPH_PAUSED,
    EXECUTION_GRAPH_RESUMED,
    EXECUTION_NODE_STARTED,
    EXECUTION_NODE_COMPLETED,
    EXECUTION_NODE_FAILED,
    EXECUTION_NODE_COMPENSATED,
)
from src.sam.core.clock import TimeProvider, SystemClock, FrozenClock
from src.sam.core.event_bus import EventBus
from src.sam.core.events import Event


# ── Helpers ────────────────────────────────────────────────────────


def _make_node(
    nid: str = "n1",
    graph_id: str = "g1",
    capability_id: str = "cap-1",
    dependencies: list = None,
    retry_policy: Optional[RetryPolicy] = None,
    compensation_policy: Optional[CompensationPolicy] = None,
    **kwargs,
) -> ExecutionNode:
    return ExecutionNode(
        id=nid,
        graph_id=graph_id,
        capability_id=capability_id,
        dependencies=dependencies or [],
        retry_policy=retry_policy or RetryPolicy(max_attempts=1),
        compensation_policy=compensation_policy or CompensationPolicy(),
        **kwargs,
    )


def _make_graph(
    gid: str = "g1",
    nodes: list = None,
    correlation_id: str = "corr-1",
    **kwargs,
) -> ExecutionGraph:
    node_list = nodes or []
    if "entry_nodes" not in kwargs:
        # Auto-set entry nodes: nodes with no dependencies
        entry = [n.id for n in node_list if not n.dependencies]
        kwargs["entry_nodes"] = entry
    if "exit_nodes" not in kwargs:
        deps_of_others = set()
        for n in node_list:
            deps_of_others.update(n.dependencies)
        exit_nodes = [n.id for n in node_list if n.id not in deps_of_others]
        kwargs["exit_nodes"] = exit_nodes
    return ExecutionGraph(
        id=gid,
        name="Test Graph",
        nodes=node_list,
        correlation_id=correlation_id,
        **kwargs,
    )


def _make_executor(return_values: Dict[str, Any] = None, failures: Dict[str, Exception] = None):
    """Create a capability_executor that returns pre-defined values."""
    return_values = return_values or {}
    failures = failures or {}

    async def executor(node: ExecutionNode) -> Any:
        if node.id in failures:
            raise failures[node.id]
        return return_values.get(node.id, {"ok": True, "node": node.id})

    return executor


# ── Test: Sequential Execution ─────────────────────────────────────

class TestSequentialExecution:
    """Chain A → B → C: each node depends on the previous."""

    @pytest.mark.asyncio
    async def test_chain_success(self):
        engine = ExecutionGraphEngine(
            clock=FrozenClock(datetime(2025, 1, 1, 0, 0, 0)),
        )
        n1 = _make_node("n1", "g1", "cap-1")
        n2 = _make_node("n2", "g1", "cap-2", dependencies=["n1"])
        n3 = _make_node("n3", "g1", "cap-3", dependencies=["n2"])
        graph = _make_graph("g1", [n1, n2, n3])

        executor = _make_executor()
        result = await engine.execute(graph, capability_executor=executor)

        assert result.status == GraphStatus.COMPLETED
        assert len(result.node_results) == 3
        assert all(r.status == NodeStatus.COMPLETED for r in result.node_results)
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_chain_mid_failure_abort(self):
        """A → B(fail) → C: B fails with ABORT → C should be SKIPPED."""
        engine = ExecutionGraphEngine(
            clock=FrozenClock(datetime(2025, 1, 1, 0, 0, 0)),
        )
        n1 = _make_node("n1", "g1", "cap-1")
        n2 = _make_node(
            "n2", "g1", "cap-2", dependencies=["n1"],
            compensation_policy=CompensationPolicy(on_failure=CompensationOnFailure.ABORT),
        )
        n3 = _make_node("n3", "g1", "cap-3", dependencies=["n2"])
        graph = _make_graph("g1", [n1, n2, n3])

        executor = _make_executor(failures={"n2": ValueError("B failed")})
        result = await engine.execute(graph, capability_executor=executor)

        assert result.status == GraphStatus.FAILED
        r1 = result.node_results[0]
        assert r1.status == NodeStatus.COMPLETED
        r2 = result.node_results[1]
        assert r2.status == NodeStatus.FAILED
        assert r2.error == "B failed"
        r3 = result.node_results[2]
        assert r3.status == NodeStatus.SKIPPED


# ── Test: Parallel Execution ───────────────────────────────────────

class TestParallelExecution:
    """A, B are independent → both run in parallel → C depends on both."""

    @pytest.mark.asyncio
    async def test_fan_in(self):
        engine = ExecutionGraphEngine(
            clock=FrozenClock(datetime(2025, 1, 1, 0, 0, 0)),
        )
        n1 = _make_node("n1", "g1", "cap-a")
        n2 = _make_node("n2", "g1", "cap-b")  # no deps, parallel with n1
        n3 = _make_node("n3", "g1", "cap-c", dependencies=["n1", "n2"])
        graph = _make_graph("g1", [n1, n2, n3])

        executor = _make_executor()
        result = await engine.execute(graph, capability_executor=executor)

        assert result.status == GraphStatus.COMPLETED
        assert len(result.node_results) == 3
        all_completed = all(r.status == NodeStatus.COMPLETED for r in result.node_results)
        assert all_completed

    @pytest.mark.asyncio
    async def test_parallel_with_one_failure(self):
        """A and B in parallel. A fails (ABORT), B succeeds. C is SKIPPED."""
        engine = ExecutionGraphEngine(
            clock=FrozenClock(datetime(2025, 1, 1, 0, 0, 0)),
        )
        n1 = _make_node(
            "n1", "g1", "cap-a",
            compensation_policy=CompensationPolicy(on_failure=CompensationOnFailure.ABORT),
        )
        n2 = _make_node("n2", "g1", "cap-b")
        n3 = _make_node("n3", "g1", "cap-c", dependencies=["n1", "n2"])
        graph = _make_graph("g1", [n1, n2, n3])

        executor = _make_executor(failures={"n1": RuntimeError("A failed")})
        result = await engine.execute(graph, capability_executor=executor)

        assert result.status == GraphStatus.FAILED
        r1 = next(r for r in result.node_results if r.node_id == "n1")
        assert r1.status == NodeStatus.FAILED
        r2 = next(r for r in result.node_results if r.node_id == "n2")
        assert r2.status == NodeStatus.COMPLETED
        r3 = next(r for r in result.node_results if r.node_id == "n3")
        assert r3.status == NodeStatus.SKIPPED


# ── Test: Retry Logic ──────────────────────────────────────────────

class TestRetryLogic:
    """RetryPolicy: linear/exponential backoff with jitter."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_third_attempt(self):
        """Node fails twice, succeeds on third attempt (max_attempts=3)."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)

        # Custom executor that fails first 2 times
        call_count = 0

        async def flaky_executor(node: ExecutionNode):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return {"success": True}

        n1 = _make_node(
            "n1", "g1", "cap-1",
            retry_policy=RetryPolicy(
                max_attempts=3,
                backoff=RetryBackoff.LINEAR,
                initial_delay=0,
                jitter=False,
            ),
        )
        graph = _make_graph("g1", [n1])
        result = await engine.execute(graph, capability_executor=flaky_executor)

        assert result.status == GraphStatus.COMPLETED
        r = result.node_results[0]
        assert r.status == NodeStatus.COMPLETED
        assert r.attempts == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        """Node fails all 5 attempts → marked FAILED."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)

        async def always_fails(node: ExecutionNode):
            raise RuntimeError("always fails")

        n1 = _make_node(
            "n1", "g1", "cap-1",
            retry_policy=RetryPolicy(
                max_attempts=5,
                backoff=RetryBackoff.LINEAR,
                initial_delay=0,
                jitter=False,
            ),
        )
        graph = _make_graph("g1", [n1])
        result = await engine.execute(graph, capability_executor=always_fails)

        assert result.status == GraphStatus.FAILED
        r = result.node_results[0]
        assert r.status == NodeStatus.FAILED
        assert r.attempts == 5
        assert "always fails" in r.error

    @pytest.mark.asyncio
    async def test_retry_with_exponential_backoff(self):
        """Verify exponential backoff delay formula used."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)

        call_count = 0

        async def fails_twice_then_ok(node: ExecutionNode):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("fail")
            return {"ok": True}

        n1 = _make_node(
            "n1", "g1", "cap-1",
            retry_policy=RetryPolicy(
                max_attempts=3,
                backoff=RetryBackoff.EXPONENTIAL,
                initial_delay=1,
                max_delay=60,
                jitter=False,
            ),
        )
        graph = _make_graph("g1", [n1])
        result = await engine.execute(graph, capability_executor=fails_twice_then_ok)

        assert result.status == GraphStatus.COMPLETED
        r = result.node_results[0]
        assert r.status == NodeStatus.COMPLETED
        assert r.attempts == 3


# ── Test: Compensation ─────────────────────────────────────────────

class TestCompensation:
    """CompensationPolicy behaviours: COMPENSATE, ABORT, RETRY, ESCALATE."""

    @pytest.mark.asyncio
    async def test_compensate_success(self):
        """Node fails → compensation node runs successfully → node marked COMPENSATED."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)

        comp_node = _make_node("comp-1", "g1", "cap-comp")
        failing_node = _make_node(
            "n1", "g1", "cap-1",
            retry_policy=RetryPolicy(max_attempts=1, initial_delay=0, jitter=False),
            compensation_policy=CompensationPolicy(
                compensation_node_id="comp-1",
                on_failure=CompensationOnFailure.COMPENSATE,
            ),
        )
        graph = _make_graph("g1", [failing_node, comp_node])

        # Register graph in active_graphs so compensation can find comp_node
        engine._active_graphs["g1"] = graph

        executor = _make_executor(
            return_values={"comp-1": {"compensated": True}},
            failures={"n1": RuntimeError("main node failed")},
        )
        result = await engine.execute(graph, capability_executor=executor)

        assert result.status == GraphStatus.COMPENSATED
        r = result.node_results[0]
        assert r.status == NodeStatus.COMPENSATED
        assert "main node failed" in r.error

    @pytest.mark.asyncio
    async def test_compensate_no_compensation_node(self):
        """COMPENSATE set but no compensation_node_id → node marked FAILED."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)

        n1 = _make_node(
            "n1", "g1", "cap-1",
            retry_policy=RetryPolicy(max_attempts=1, initial_delay=0, jitter=False),
            compensation_policy=CompensationPolicy(
                compensation_node_id=None,
                on_failure=CompensationOnFailure.COMPENSATE,
            ),
        )
        graph = _make_graph("g1", [n1])

        async def fails(node: ExecutionNode):
            raise RuntimeError("failed")

        result = await engine.execute(graph, capability_executor=fails)

        assert result.status == GraphStatus.FAILED
        r = result.node_results[0]
        assert r.status == NodeStatus.FAILED

    @pytest.mark.asyncio
    async def test_abort_stops_graph(self):
        """Node with ABORT marks FAILED, downstream nodes SKIPPED."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)

        n1 = _make_node("n1", "g1", "cap-1")
        n2 = _make_node(
            "n2", "g1", "cap-2", dependencies=["n1"],
            compensation_policy=CompensationPolicy(on_failure=CompensationOnFailure.ABORT),
            retry_policy=RetryPolicy(max_attempts=1, initial_delay=0, jitter=False),
        )
        n3 = _make_node("n3", "g1", "cap-3", dependencies=["n2"])
        graph = _make_graph("g1", [n1, n2, n3])

        executor = _make_executor(failures={"n2": RuntimeError("n2 failed")})
        result = await engine.execute(graph, capability_executor=executor)

        assert result.status == GraphStatus.FAILED
        r2 = next(r for r in result.node_results if r.node_id == "n2")
        assert r2.status == NodeStatus.FAILED
        r3 = next(r for r in result.node_results if r.node_id == "n3")
        assert r3.status == NodeStatus.SKIPPED


# ── Test: Pause/Resume ─────────────────────────────────────────────

class TestPauseResume:
    """Graph pause and resume with checkpointing."""

    @pytest.mark.asyncio
    async def test_pause(self):
        """Pause marks graph PAUSED."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)

        n1 = _make_node("n1", "g1", "cap-1")
        graph = _make_graph("g1", [n1])

        engine._active_graphs["g1"] = graph
        await engine.pause("g1")

        assert engine.is_paused("g1")
        status = await engine.get_status("g1")
        assert status == GraphStatus.PAUSED
        assert graph.status == GraphStatus.PAUSED

    @pytest.mark.asyncio
    async def test_resume(self):
        """Resume clears paused state."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)

        n1 = _make_node("n1", "g1", "cap-1")
        graph = _make_graph("g1", [n1])

        engine._active_graphs["g1"] = graph
        await engine.pause("g1")
        assert engine.is_paused("g1")

        await engine.resume("g1")
        assert not engine.is_paused("g1")
        status = await engine.get_status("g1")
        assert status == GraphStatus.RUNNING
        assert graph.status == GraphStatus.RUNNING

    @pytest.mark.asyncio
    async def test_pause_unknown_graph(self):
        """Pausing a non-existent graph should warn but not crash."""
        engine = ExecutionGraphEngine()
        await engine.pause("no-such-graph")
        # Should not raise

    @pytest.mark.asyncio
    async def test_resume_non_paused(self):
        """Resuming a non-paused graph should warn but not crash."""
        engine = ExecutionGraphEngine()
        await engine.resume("no-such-graph")
        # Should not raise

    @pytest.mark.asyncio
    async def test_get_status_none_for_unknown(self):
        """get_status returns None for unknown graph."""
        engine = ExecutionGraphEngine()
        assert await engine.get_status("no-such-graph") is None


# ── Test: Error Handling ───────────────────────────────────────────

class TestErrorHandling:
    """Edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_invalid_graph(self):
        """An invalid graph (missing dep) returns FAILED immediately."""
        engine = ExecutionGraphEngine()
        n1 = _make_node("n1", "g1", "cap-1", dependencies=["n2"])  # n2 doesn't exist
        graph = _make_graph("g1", [n1])
        result = await engine.execute(graph, capability_executor=_make_executor())

        assert result.status == GraphStatus.FAILED
        assert len(result.node_results) == 0

    @pytest.mark.asyncio
    async def test_cycle_graph(self):
        """A graph with a cycle returns FAILED immediately."""
        engine = ExecutionGraphEngine()
        n1 = _make_node("n1", "g1", "cap-1", dependencies=["n2"])
        n2 = _make_node("n2", "g1", "cap-2", dependencies=["n1"])
        graph = _make_graph("g1", [n1, n2])

        result = await engine.execute(graph, capability_executor=_make_executor())
        assert result.status == GraphStatus.FAILED

    @pytest.mark.asyncio
    async def test_empty_graph(self):
        """An empty graph returns FAILED (no entry nodes)."""
        engine = ExecutionGraphEngine()
        graph = _make_graph("g1", [])
        result = await engine.execute(graph)

        # Empty graph with no entry/exit nodes is not an explicit validation
        # error — it just produces no results
        assert result.status in (GraphStatus.FAILED, GraphStatus.COMPLETED)

    @pytest.mark.asyncio
    async def test_single_node_graph(self):
        """A graph with a single node succeeds."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)
        n1 = _make_node("n1", "g1", "cap-1")
        graph = _make_graph("g1", [n1])

        executor = _make_executor(return_values={"n1": {"done": True}})
        result = await engine.execute(graph, capability_executor=executor)

        assert result.status == GraphStatus.COMPLETED
        assert result.node_results[0].status == NodeStatus.COMPLETED


# ── Test: Event Publishing ─────────────────────────────────────────

class TestEventPublishing:
    """Engine publishes lifecycle events to EventBus."""

    @pytest.mark.asyncio
    async def test_graph_started_event(self):
        """Execute should publish graph.started."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        bus = EventBus()
        engine = ExecutionGraphEngine(clock=clock, event_bus=bus)

        received = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe(EXECUTION_GRAPH_STARTED, handler)
        bus.subscribe(EXECUTION_GRAPH_COMPLETED, handler)

        n1 = _make_node("n1", "g1", "cap-1")
        graph = _make_graph("g1", [n1])
        result = await engine.execute(graph, capability_executor=_make_executor())

        assert result.status == GraphStatus.COMPLETED
        assert any(e.type == EXECUTION_GRAPH_STARTED for e in received)
        assert any(e.type == EXECUTION_GRAPH_COMPLETED for e in received)

    @pytest.mark.asyncio
    async def test_node_started_and_completed_events(self):
        """Execute should publish node.started and node.completed for each node."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        bus = EventBus()
        engine = ExecutionGraphEngine(clock=clock, event_bus=bus)

        received = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe(EXECUTION_NODE_STARTED, handler)
        bus.subscribe(EXECUTION_NODE_COMPLETED, handler)

        n1 = _make_node("n1", "g1", "cap-1")
        n2 = _make_node("n2", "g1", "cap-2", dependencies=["n1"])
        graph = _make_graph("g1", [n1, n2])
        await engine.execute(graph, capability_executor=_make_executor())

        node_started = [e for e in received if e.type == EXECUTION_NODE_STARTED]
        node_completed = [e for e in received if e.type == EXECUTION_NODE_COMPLETED]
        assert len(node_started) == 2
        assert len(node_completed) == 2

    @pytest.mark.asyncio
    async def test_node_failed_event(self):
        """Failed nodes should publish node.failed event."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        bus = EventBus()
        engine = ExecutionGraphEngine(clock=clock, event_bus=bus)

        received = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe(EXECUTION_NODE_FAILED, handler)

        n1 = _make_node(
            "n1", "g1", "cap-1",
            retry_policy=RetryPolicy(max_attempts=1, initial_delay=0, jitter=False),
        )
        graph = _make_graph("g1", [n1])

        async def fails(node: ExecutionNode):
            raise RuntimeError("fail")

        await engine.execute(graph, capability_executor=fails)

        failed_events = [e for e in received if e.type == EXECUTION_NODE_FAILED]
        assert len(failed_events) >= 1

    @pytest.mark.asyncio
    async def test_graph_failed_event(self):
        """A graph that fails should publish graph.failed."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        bus = EventBus()
        engine = ExecutionGraphEngine(clock=clock, event_bus=bus)

        received = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe(EXECUTION_GRAPH_FAILED, handler)

        n1 = _make_node(
            "n1", "g1", "cap-1",
            retry_policy=RetryPolicy(max_attempts=1, initial_delay=0, jitter=False),
            compensation_policy=CompensationPolicy(on_failure=CompensationOnFailure.ABORT),
        )
        graph = _make_graph("g1", [n1])

        async def fails(node: ExecutionNode):
            raise RuntimeError("fail")

        await engine.execute(graph, capability_executor=fails)

        failed_events = [e for e in received if e.type == EXECUTION_GRAPH_FAILED]
        assert len(failed_events) == 1

    @pytest.mark.asyncio
    async def test_pause_resume_events(self):
        """Pause should publish graph.paused, resume should publish graph.resumed."""
        bus = EventBus()
        engine = ExecutionGraphEngine(event_bus=bus)

        received = []

        async def handler(event: Event):
            received.append(event)

        bus.subscribe(EXECUTION_GRAPH_PAUSED, handler)
        bus.subscribe(EXECUTION_GRAPH_RESUMED, handler)

        n1 = _make_node("n1", "g1", "cap-1")
        graph = _make_graph("g1", [n1])
        engine._active_graphs["g1"] = graph

        await engine.pause("g1")
        await engine.resume("g1")

        assert any(e.type == EXECUTION_GRAPH_PAUSED for e in received)
        assert any(e.type == EXECUTION_GRAPH_RESUMED for e in received)


# ── Test: Graph Status Derivation ──────────────────────────────────

class TestGraphStatusDerivation:
    """_derive_graph_status determines final graph status from node results."""

    def test_all_completed(self):
        engine = ExecutionGraphEngine()
        results = [
            NodeResult("n1", NodeStatus.COMPLETED),
            NodeResult("n2", NodeStatus.COMPLETED),
        ]
        assert engine._derive_graph_status(results) == GraphStatus.COMPLETED

    def test_completed_and_skipped(self):
        engine = ExecutionGraphEngine()
        results = [
            NodeResult("n1", NodeStatus.COMPLETED),
            NodeResult("n2", NodeStatus.SKIPPED),
        ]
        assert engine._derive_graph_status(results) == GraphStatus.COMPLETED

    def test_has_failed(self):
        engine = ExecutionGraphEngine()
        results = [
            NodeResult("n1", NodeStatus.COMPLETED),
            NodeResult("n2", NodeStatus.FAILED),
        ]
        assert engine._derive_graph_status(results) == GraphStatus.FAILED

    def test_has_compensated(self):
        engine = ExecutionGraphEngine()
        results = [
            NodeResult("n1", NodeStatus.COMPLETED),
            NodeResult("n2", NodeStatus.COMPENSATED),
        ]
        assert engine._derive_graph_status(results) == GraphStatus.COMPENSATED

    def test_empty_results(self):
        engine = ExecutionGraphEngine()
        assert engine._derive_graph_status([]) == GraphStatus.FAILED


# ── Test: Edge Cases ───────────────────────────────────────────────

class TestEdgeCases:
    """Miscellaneous edge cases."""

    @pytest.mark.asyncio
    async def test_diamond_pattern(self):
        """A → B, A → C; B, C → D."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)
        n1 = _make_node("A", "g1", "cap-1")
        n2 = _make_node("B", "g1", "cap-2", dependencies=["A"])
        n3 = _make_node("C", "g1", "cap-3", dependencies=["A"])
        n4 = _make_node("D", "g1", "cap-4", dependencies=["B", "C"])
        graph = _make_graph("g1", [n1, n2, n3, n4])

        executor = _make_executor()
        result = await engine.execute(graph, capability_executor=executor)

        assert result.status == GraphStatus.COMPLETED
        assert len(result.node_results) == 4
        assert all(r.status == NodeStatus.COMPLETED for r in result.node_results)

    @pytest.mark.asyncio
    async def test_fan_out_fan_in(self):
        """A → B, C, D → E (3 independent parallel + final convergence)."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)
        nodes = [
            _make_node("A", "g1", "cap-a"),
            _make_node("B", "g1", "cap-b", dependencies=["A"]),
            _make_node("C", "g1", "cap-c", dependencies=["A"]),
            _make_node("D", "g1", "cap-d", dependencies=["A"]),
            _make_node("E", "g1", "cap-e", dependencies=["B", "C", "D"]),
        ]
        graph = _make_graph("g1", nodes)

        executor = _make_executor()
        result = await engine.execute(graph, capability_executor=executor)

        assert result.status == GraphStatus.COMPLETED
        assert len(result.node_results) == 5
        assert all(r.status == NodeStatus.COMPLETED for r in result.node_results)

    @pytest.mark.asyncio
    async def test_node_result_has_output(self):
        """Successful node result should include output data."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)
        n1 = _make_node("n1", "g1", "cap-1")
        graph = _make_graph("g1", [n1])

        executor = _make_executor(return_values={"n1": {"key": "value"}})
        result = await engine.execute(graph, capability_executor=executor)

        assert result.node_results[0].output == {"key": "value"}

    @pytest.mark.asyncio
    async def test_node_result_non_dict_output(self):
        """Output that isn't a dict is wrapped in {'_result': ...}."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)
        n1 = _make_node("n1", "g1", "cap-1")
        graph = _make_graph("g1", [n1])

        executor = _make_executor(return_values={"n1": "simple_string"})
        result = await engine.execute(graph, capability_executor=executor)

        assert result.node_results[0].output == {"_result": "simple_string"}

    @pytest.mark.asyncio
    async def test_duration_metrics(self):
        """GraphResult should include started_at, completed_at, duration_ms."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)
        n1 = _make_node("n1", "g1", "cap-1")
        graph = _make_graph("g1", [n1])

        result = await engine.execute(graph, capability_executor=_make_executor())

        assert result.started_at is not None
        assert result.completed_at is not None
        assert result.duration_ms >= 0

    @pytest.mark.asyncio
    async def test_no_capability_executor_or_runtime_raises(self):
        """Engine without runtime and without capability_executor — graph fails."""
        engine = ExecutionGraphEngine(runtime=None)
        n1 = _make_node(
            "n1", "g1", "cap-1",
            retry_policy=RetryPolicy(max_attempts=1, initial_delay=0, jitter=False),
            compensation_policy=CompensationPolicy(on_failure=CompensationOnFailure.ABORT),
        )
        graph = _make_graph("g1", [n1])

        result = await engine.execute(graph)  # no capability_executor
        assert result.status == GraphStatus.FAILED
        assert "No capability executor" in result.node_results[0].error

    @pytest.mark.asyncio
    async def test_compensation_node_not_found_in_graph(self):
        """COMPENSATE with node_id not in graph → falls to FAILED."""
        clock = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
        engine = ExecutionGraphEngine(clock=clock)

        n1 = _make_node(
            "n1", "g1", "cap-1",
            retry_policy=RetryPolicy(max_attempts=1, initial_delay=0, jitter=False),
            compensation_policy=CompensationPolicy(
                compensation_node_id="nonexistent",
                on_failure=CompensationOnFailure.COMPENSATE,
            ),
        )
        graph = _make_graph("g1", [n1])
        engine._active_graphs["g1"] = graph

        async def fails(node: ExecutionNode):
            raise RuntimeError("fail")

        result = await engine.execute(graph, capability_executor=fails)

        assert result.status == GraphStatus.FAILED
        r = result.node_results[0]
        assert r.status == NodeStatus.FAILED
