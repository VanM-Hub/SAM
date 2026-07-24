import asyncio
import pytest

from sam.execution.graph import ExecutionGraph
from sam.execution.node import ExecutionNode, NodeStatus
from sam.execution.decision import (
    DecisionNode,
    DecisionCondition,
    DecisionType,
)
from sam.execution.engine import ExecutionGraphEngine
from sam.execution.node import CompensationPolicy
from sam.execution.node import CompensationOnFailure


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operator, actual, expected_val, should_choose_true",
    [
        ("==", 5, 5, True),
        ("!=", 5, 3, True),
        (">", 5, 2, True),
        ("<", 1, 2, True),
        (">=", 5, 5, True),
        ("<=", 3, 4, True),
        ("contains", "hello world", "world", True),
        ("starts_with", "prefix_value", "prefix", True),
    ],
)
async def test_decision_operators(operator, actual, expected_val, should_choose_true):
    # Build a graph: start -> decision -> true_node / false_node
    graph_id = "g-ops"
    start = ExecutionNode(
        id="start",
        graph_id=graph_id,
        capability_id="cap.echo",
        inputs={"value": actual},
    )
    decision_exec = ExecutionNode(
        id="decide",
        graph_id=graph_id,
        capability_id="cap.decision",
        inputs={},
        is_decision=True,
        decision_id="d1",
        dependencies=["start"],
    )
    true_node = ExecutionNode(
        id="true",
        graph_id=graph_id,
        capability_id="cap.true",
        inputs={},
    )
    false_node = ExecutionNode(
        id="false",
        graph_id=graph_id,
        capability_id="cap.false",
        inputs={},
    )

    cond = DecisionCondition(type=DecisionType.IF_EVIDENCE, key="node.start.output.value", operator=operator, value=expected_val)
    decision = DecisionNode(id="d1", conditions=[cond], branch_targets={"0": "true"}, default_target="false")

    graph = ExecutionGraph(id=graph_id, name="ops", nodes=[start, decision_exec, true_node, false_node], decision_nodes={"d1": decision}, entry_nodes=["start"], exit_nodes=["true", "false"], correlation_id="c1")

    # capability executor: start returns the provided input value
    def capability_executor(node):
        if node.id == "start":
            return {"value": node.inputs.get("value")}
        return {"ran": node.id}

    engine = ExecutionGraphEngine()
    result = await engine.execute(graph, capability_executor=capability_executor)

    # Verify branching: true executed (COMPLETED) and false skipped
    node_map = graph.node_map
    if should_choose_true:
        assert node_map["true"].status == NodeStatus.COMPLETED
        assert node_map["false"].status in (NodeStatus.SKIPPED,)
    else:
        assert node_map["false"].status == NodeStatus.COMPLETED


@pytest.mark.asyncio
async def test_default_target_when_no_match():
    graph_id = "g-default"
    start = ExecutionNode(id="start", graph_id=graph_id, capability_id="cap.echo", inputs={"name": "van"})
    decision_exec = ExecutionNode(id="decide", graph_id=graph_id, capability_id="cap.d", inputs={}, is_decision=True, decision_id="d2", dependencies=["start"]) 
    a = ExecutionNode(id="a", graph_id=graph_id, capability_id="cap.a", inputs={})
    b = ExecutionNode(id="b", graph_id=graph_id, capability_id="cap.b", inputs={})

    cond = DecisionCondition(type=DecisionType.IF_EVIDENCE, key="node.start.output.name", operator="==", value="nobody")
    decision = DecisionNode(id="d2", conditions=[cond], branch_targets={"0": "a"}, default_target="b")

    graph = ExecutionGraph(id=graph_id, name="def", nodes=[start, decision_exec, a, b], decision_nodes={"d2": decision}, entry_nodes=["start"], exit_nodes=["a", "b"], correlation_id="c2")

    def capability_executor(node):
        if node.id == "start":
            return {"name": node.inputs.get("name")}
        return {"ran": node.id}

    engine = ExecutionGraphEngine()
    result = await engine.execute(graph, capability_executor=capability_executor)

    assert graph.node_map["b"].status == NodeStatus.COMPLETED
    assert graph.node_map["a"].status == NodeStatus.SKIPPED


@pytest.mark.asyncio
async def test_validation_and_missing_decision_reference():
    # Decision branch target points to non-existent node
    d = DecisionNode(id="d3", conditions=[DecisionCondition(type=DecisionType.IF_EVIDENCE, key="x", operator="==", value=1)], branch_targets={"0": "nope"}, default_target=None)
    start = ExecutionNode(id="s", graph_id="g-val", capability_id="cap.x", inputs={})
    graph = ExecutionGraph(id="g-val", name="val", nodes=[start], decision_nodes={"d3": d}, entry_nodes=["s"], exit_nodes=["s"], correlation_id="c3")
    errors = graph.validate()
    assert any("branch target 'nope'" in e for e in errors)

    # Node marked as decision but no decision_id
    bad_node = ExecutionNode(id="b", graph_id="g2", capability_id="cap.x", inputs={}, is_decision=True)
    graph2 = ExecutionGraph(id="g2", name="g2", nodes=[bad_node], decision_nodes={}, entry_nodes=["b"], exit_nodes=["b"], correlation_id="c4")
    errors2 = graph2.validate()
    assert any("is_decision=True but no decision_id" in e for e in errors2)


@pytest.mark.asyncio
async def test_if_status_condition_matches_failed_node():
    # Node 'bad' will fail; decision checks its status
    graph_id = "g-status"
    bad = ExecutionNode(id="bad", graph_id=graph_id, capability_id="cap.bad", inputs={})
    # avoid ABORT on failure
    bad.compensation_policy = CompensationPolicy(compensation_node_id=None, on_failure=CompensationOnFailure.RETRY)

    decision_exec = ExecutionNode(id="decide", graph_id=graph_id, capability_id="cap.d", inputs={}, is_decision=True, decision_id="d4", dependencies=["bad"]) 
    t = ExecutionNode(id="t", graph_id=graph_id, capability_id="cap.t", inputs={})
    f = ExecutionNode(id="f", graph_id=graph_id, capability_id="cap.f", inputs={})

    cond = DecisionCondition(type=DecisionType.IF_STATUS, key="node.bad.status", operator="==", value="FAILED")
    decision = DecisionNode(id="d4", conditions=[cond], branch_targets={"0": "t"}, default_target="f")

    graph = ExecutionGraph(id=graph_id, name="status", nodes=[bad, decision_exec, t, f], decision_nodes={"d4": decision}, entry_nodes=["bad"], exit_nodes=["t", "f"], correlation_id="c5")

    def capability_executor(node):
        if node.id == "bad":
            raise RuntimeError("boom")
        return {"ok": True}

    engine = ExecutionGraphEngine()
    result = await engine.execute(graph, capability_executor=capability_executor)

    # decision should route to 't' because bad failed
    assert graph.node_map["t"].status == NodeStatus.COMPLETED
    assert graph.node_map["f"].status == NodeStatus.SKIPPED
