"""
Tests for Execution Graph and Execution Node models.

Covers:
- Model creation and validation
- RetryPolicy delay calculation
- CompensationPolicy defaults
- ExecutionGraph structure (edges, upstream/downstream)
- Dependency cycle detection
- Graph validation (missing deps, entry/exit mismatch)
"""

from __future__ import annotations

import json

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
    ExecutionEdge,
)


# ── Helpers ────────────────────────────────────────────────────────


def _make_node(
    nid: str = "n1",
    graph_id: str = "g1",
    capability_id: str = "cap-1",
    dependencies: list = None,
    **kwargs,
) -> ExecutionNode:
    return ExecutionNode(
        id=nid,
        graph_id=graph_id,
        capability_id=capability_id,
        dependencies=dependencies or [],
        **kwargs,
    )


def _make_graph(
    gid: str = "g1",
    nodes: list = None,
    correlation_id: str = "corr-1",
    **kwargs,
) -> ExecutionGraph:
    return ExecutionGraph(
        id=gid,
        name="Test Graph",
        nodes=nodes or [],
        entry_nodes=kwargs.pop("entry_nodes", []),
        exit_nodes=kwargs.pop("exit_nodes", []),
        correlation_id=correlation_id,
        **kwargs,
    )


# ── ExecutionNode / RetryPolicy / CompensationPolicy ───────────────


class TestNodeModel:
    def test_basic_creation(self):
        node = _make_node()
        assert node.id == "n1"
        assert node.graph_id == "g1"
        assert node.capability_id == "cap-1"
        assert node.status == NodeStatus.PENDING
        assert node.inputs == {}
        assert node.outputs is None
        assert node.dependencies == []
        assert node.evidence_ids == []
        assert node.started_at is None
        assert node.completed_at is None

    def test_with_optional_fields(self):
        from datetime import datetime

        now = datetime.now()
        node = _make_node(
            nid="n2",
            inputs={"key": "value"},
            outputs={"result": 42},
            evidence_ids=["ev-1"],
            started_at=now,
            completed_at=now,
        )
        assert node.inputs == {"key": "value"}
        assert node.outputs == {"result": 42}
        assert node.evidence_ids == ["ev-1"]
        assert node.started_at == now
        assert node.completed_at == now

    def test_default_retry_policy(self):
        node = _make_node()
        rp = node.retry_policy
        assert rp.max_attempts == 3
        assert rp.backoff == RetryBackoff.EXPONENTIAL
        assert rp.initial_delay == 1
        assert rp.max_delay == 60
        assert rp.jitter is True

    def test_default_compensation_policy(self):
        node = _make_node()
        cp = node.compensation_policy
        assert cp.compensation_node_id is None
        assert cp.on_failure == CompensationOnFailure.ABORT

    def test_status_lifecycle(self):
        node = _make_node()
        assert node.status == NodeStatus.PENDING
        node.status = NodeStatus.RUNNING
        assert node.status == NodeStatus.RUNNING
        node.status = NodeStatus.COMPLETED
        assert node.status == NodeStatus.COMPLETED

    def test_is_terminal(self):
        for status in (NodeStatus.COMPLETED, NodeStatus.FAILED,
                       NodeStatus.COMPENSATED, NodeStatus.SKIPPED):
            node = _make_node()
            node.status = status
            assert node.is_terminal is True, f"{status.value} should be terminal"

    def test_is_not_terminal(self):
        for status in (NodeStatus.PENDING, NodeStatus.RUNNING):
            node = _make_node()
            node.status = status
            assert node.is_terminal is False, f"{status.value} should not be terminal"

    def test_is_ready(self):
        node = _make_node()
        assert node.is_ready is True

    def test_extra_fields_forbidden(self):
        with pytest.raises(Exception):
            ExecutionNode(
                id="n1", graph_id="g1", capability_id="c1",
                extra_field="should fail",
            )

    def test_extra_fields_forbidden_retry_policy(self):
        with pytest.raises(Exception):
            RetryPolicy(unknown=True)

    def test_extra_fields_forbidden_compensation_policy(self):
        with pytest.raises(Exception):
            CompensationPolicy(extra=42)


class TestRetryPolicy:
    def test_linear_backoff(self):
        rp = RetryPolicy(backoff=RetryBackoff.LINEAR, initial_delay=5, max_delay=60, jitter=False)
        # attempt 1 → delay = 5 * 1 = 5, attempt 3 → delay = 5 * 3 = 15
        assert rp.delay_for_attempt(1) == 5.0
        assert rp.delay_for_attempt(3) == 15.0

    def test_exponential_backoff(self):
        rp = RetryPolicy(backoff=RetryBackoff.EXPONENTIAL, initial_delay=1, max_delay=60, jitter=False)
        # attempt 1 → 1 * 2^0 = 1, attempt 3 → 1 * 2^2 = 4, attempt 5 → 1 * 2^4 = 16
        assert rp.delay_for_attempt(1) == 1.0
        assert rp.delay_for_attempt(3) == 4.0
        assert rp.delay_for_attempt(5) == 16.0

    def test_max_delay_cap(self):
        rp = RetryPolicy(initial_delay=1, max_delay=4, jitter=False)
        # attempt 4 → 1 * 2^3 = 8 → capped at 4
        assert rp.delay_for_attempt(4) == 4.0

    def test_jitter_adds_variation(self):
        rp = RetryPolicy(initial_delay=10, jitter=True)
        delays = [rp.delay_for_attempt(1) for _ in range(20)]
        # With jitter, delays should vary around 5–15 (10 * 0.5 to 10 * 1.5)
        assert any(d != delays[0] for d in delays), "Jitter should produce variation"

    def test_min_zero(self):
        rp = RetryPolicy(initial_delay=0, backoff=RetryBackoff.LINEAR, jitter=False)
        assert rp.delay_for_attempt(1) == 0.0


class TestCompensationPolicy:
    def test_with_compensation_node(self):
        cp = CompensationPolicy(
            compensation_node_id="cn1",
            on_failure=CompensationOnFailure.COMPENSATE,
        )
        assert cp.compensation_node_id == "cn1"
        assert cp.on_failure == CompensationOnFailure.COMPENSATE

    def test_escalate_on_failure(self):
        cp = CompensationPolicy(on_failure=CompensationOnFailure.ESCALATE)
        assert cp.compensation_node_id is None
        assert cp.on_failure == CompensationOnFailure.ESCALATE


# ── ExecutionGraph ─────────────────────────────────────────────────


class TestExecutionGraph:
    def test_empty_graph(self):
        g = _make_graph()
        assert g.id == "g1"
        assert g.name == "Test Graph"
        assert g.nodes == []
        assert g.status == GraphStatus.CREATED
        assert g.correlation_id == "corr-1"
        assert g.node_map == {}

    def test_graph_with_nodes(self):
        n1 = _make_node("n1", "g1", "cap-a")
        n2 = _make_node("n2", "g1", "cap-b", dependencies=["n1"])
        g = _make_graph("g1", [n1, n2])
        assert len(g.nodes) == 2
        assert g.node_map["n1"] is n1
        assert g.node_map["n2"] is n2

    def test_get_node(self):
        n1 = _make_node("n1", "g1", "cap-a")
        g = _make_graph("g1", [n1])
        assert g.get_node("n1") is n1
        assert g.get_node("missing") is None

    def test_edges(self):
        n1 = _make_node("n1", "g1", "cap-a")
        n2 = _make_node("n2", "g1", "cap-b", dependencies=["n1"])
        n3 = _make_node("n3", "g1", "cap-c", dependencies=["n1"])
        g = _make_graph("g1", [n1, n2, n3])
        edges = g.edges
        assert len(edges) == 2
        edge_ids = {(e.from_node, e.to_node) for e in edges}
        assert ("n1", "n2") in edge_ids
        assert ("n1", "n3") in edge_ids

    def test_downstream(self):
        n1 = _make_node("n1", "g1", "cap-a")
        n2 = _make_node("n2", "g1", "cap-b", dependencies=["n1"])
        n3 = _make_node("n3", "g1", "cap-c", dependencies=["n1"])
        g = _make_graph("g1", [n1, n2, n3])
        ds = g.downstream("n1")
        assert set(ds) == {"n2", "n3"}
        assert g.downstream("n2") == []

    def test_upstream(self):
        n1 = _make_node("n1", "g1", "cap-a")
        n2 = _make_node("n2", "g1", "cap-b", dependencies=["n1"])
        g = _make_graph("g1", [n1, n2])
        assert g.upstream("n1") == []
        assert g.upstream("n2") == ["n1"]

    def test_metadata(self):
        g = _make_graph(metadata={"owner": "alice", "priority": 5})
        assert g.metadata == {"owner": "alice", "priority": 5}

    def test_extra_fields_forbidden(self):
        with pytest.raises(Exception):
            ExecutionGraph(
                id="g1", name="g", nodes=[],
                entry_nodes=[], exit_nodes=[],
                correlation_id="c1", bad=True,
            )


# ── Graph Validation ───────────────────────────────────────────────


class TestGraphValidation:
    def test_valid_simple_graph(self):
        n1 = _make_node("n1", "g1", "cap-a")
        n2 = _make_node("n2", "g1", "cap-b", dependencies=["n1"])
        g = _make_graph("g1", [n1, n2], entry_nodes=["n1"], exit_nodes=["n2"])
        assert g.is_valid() is True
        assert g.validate() == []

    def test_missing_dependency_reference(self):
        """Node depends on a non-existent node."""
        n1 = _make_node("n1", "g1", "cap-a", dependencies=["ghost"])
        g = _make_graph("g1", [n1])
        errors = g.validate()
        assert any("non-existent" in e or "ghost" in e for e in errors)

    def test_cycle_direct(self):
        """A → B → A (direct cycle)."""
        n1 = _make_node("n1", "g1", "cap-a", dependencies=["n2"])
        n2 = _make_node("n2", "g1", "cap-b", dependencies=["n1"])
        g = _make_graph("g1", [n1, n2])
        errors = g.validate()
        assert any("cycle" in e.lower() for e in errors)

    def test_cycle_transitive(self):
        """A → B → C → A (3-node cycle)."""
        n1 = _make_node("n1", "g1", "cap-a", dependencies=["n3"])
        n2 = _make_node("n2", "g1", "cap-b", dependencies=["n1"])
        n3 = _make_node("n3", "g1", "cap-c", dependencies=["n2"])
        g = _make_graph("g1", [n1, n2, n3])
        errors = g.validate()
        assert any("cycle" in e.lower() for e in errors)

    def test_entry_node_has_dependencies(self):
        """Entry node with dependencies is invalid."""
        n1 = _make_node("n1", "g1", "cap-a")
        n2 = _make_node("n2", "g1", "cap-b", dependencies=["n1"])
        g = _make_graph("g1", [n1, n2], entry_nodes=["n2"], exit_nodes=["n2"])
        errors = g.validate()
        assert any("entry" in e.lower() or "dependency" in e.lower() for e in errors)

    def test_exit_node_has_downstream(self):
        """Exit node that other nodes depend on is invalid."""
        n1 = _make_node("n1", "g1", "cap-a")
        n2 = _make_node("n2", "g1", "cap-b", dependencies=["n1"])
        g = _make_graph("g1", [n1, n2], entry_nodes=["n1"], exit_nodes=["n1"])
        errors = g.validate()
        assert any("exit" in e.lower() for e in errors)

    def test_entry_node_missing(self):
        """Entry node ID not in nodes list."""
        n1 = _make_node("n1", "g1", "cap-a")
        g = _make_graph("g1", [n1], entry_nodes=["ghost"], exit_nodes=["n1"])
        errors = g.validate()
        assert any("entry" in e.lower() and "not found" in e.lower() for e in errors)

    def test_exit_node_missing(self):
        """Exit node ID not in nodes list."""
        n1 = _make_node("n1", "g1", "cap-a")
        g = _make_graph("g1", [n1], entry_nodes=["n1"], exit_nodes=["ghost"])
        errors = g.validate()
        assert any("exit" in e.lower() and "not found" in e.lower() for e in errors)

    def test_diamond_graph_valid(self):
        """A → B, A → C, B → D, C → D (diamond)."""
        a = _make_node("A", "g1", "cap-a")
        b = _make_node("B", "g1", "cap-b", dependencies=["A"])
        c = _make_node("C", "g1", "cap-c", dependencies=["A"])
        d = _make_node("D", "g1", "cap-d", dependencies=["B", "C"])
        g = _make_graph("g1", [a, b, c, d], entry_nodes=["A"], exit_nodes=["D"])
        assert g.is_valid() is True

    def test_self_loop_detected(self):
        """A node depending on itself should be caught."""
        n1 = _make_node("n1", "g1", "cap-a", dependencies=["n1"])
        g = _make_graph("g1", [n1])
        errors = g.validate()
        assert any("cycle" in e.lower() for e in errors)


# ── Graph Status ────────────────────────────────────────────────────


class TestGraphStatus:
    def test_initial_is_created(self):
        g = _make_graph()
        assert g.status == GraphStatus.CREATED

    def test_transitions(self):
        g = _make_graph()
        for s in GraphStatus:
            g.status = s
            assert g.status == s


# ── Edge Model ──────────────────────────────────────────────────────


class TestEdge:
    def test_edge_creation(self):
        e = ExecutionEdge(from_node="A", to_node="B")
        assert e.from_node == "A"
        assert e.to_node == "B"

    def test_edge_extra_forbidden(self):
        with pytest.raises(Exception):
            ExecutionEdge(from_node="A", to_node="B", extra="no")


# ── Integration: Complex Graph ──────────────────────────────────────


class TestComplexGraph:
    def test_fan_out_fan_in(self):
        """Start → A, Start → B, Start → C, A → End, B → End, C → End"""
        nodes = [
            _make_node("Start", "g1", "cap-start"),
            _make_node("A", "g1", "cap-a", dependencies=["Start"]),
            _make_node("B", "g1", "cap-b", dependencies=["Start"]),
            _make_node("C", "g1", "cap-c", dependencies=["Start"]),
            _make_node("End", "g1", "cap-end", dependencies=["A", "B", "C"]),
        ]
        g = _make_graph(
            "g1",
            nodes,
            entry_nodes=["Start"],
            exit_nodes=["End"],
        )
        assert g.is_valid() is True
        assert len(g.edges) == 6
        assert set(g.downstream("Start")) == {"A", "B", "C"}
        assert g.upstream("End") == ["A", "B", "C"]

    def test_chain_of_five(self):
        """n1→n2→n3→n4→n5"""
        nodes = [
            _make_node("n1", "g1", "cap-1"),
            _make_node("n2", "g1", "cap-2", dependencies=["n1"]),
            _make_node("n3", "g1", "cap-3", dependencies=["n2"]),
            _make_node("n4", "g1", "cap-4", dependencies=["n3"]),
            _make_node("n5", "g1", "cap-5", dependencies=["n4"]),
        ]
        g = _make_graph(
            "g1", nodes, entry_nodes=["n1"], exit_nodes=["n5"]
        )
        assert g.is_valid() is True
        assert len(g.edges) == 4

    def test_multiple_entry_multiple_exit(self):
        """E1→M→X1, E2→M, M→X2"""
        nodes = [
            _make_node("E1", "g1", "cap-e1"),
            _make_node("E2", "g1", "cap-e2"),
            _make_node("M", "g1", "cap-m", dependencies=["E1", "E2"]),
            _make_node("X1", "g1", "cap-x1", dependencies=["M"]),
            _make_node("X2", "g1", "cap-x2", dependencies=["M"]),
        ]
        g = _make_graph(
            "g1", nodes,
            entry_nodes=["E1", "E2"],
            exit_nodes=["X1", "X2"],
        )
        assert g.is_valid() is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
