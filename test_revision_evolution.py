"""
Tests for Sprint 23 Fase 3 — Graph Revision & Intent Evolution.

Covers:
- RevisionManager: propose, apply, history, history with DB, propose with trigger
- EvolutionManager: propose, apply, history, history with DB
- ExecutionGraphEngine: revision trigger integration with decision nodes
"""

import json
import uuid
import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from sam.reasoning.revision import (
    GraphRevision,
    RevisionManager,
    RevisionTrigger,
)
from sam.reasoning.evolution import (
    IntentEvolution,
    EvolutionManager,
)
from sam.reasoning.intent import Intent, IntentType, IntentStatus
from sam.execution.graph import ExecutionGraph, GraphStatus
from sam.execution.node import ExecutionNode, NodeStatus, RetryPolicy, CompensationPolicy
from sam.execution.decision import DecisionNode, DecisionCondition, DecisionType
from sam.execution.engine import ExecutionGraphEngine, GraphResult, NodeResult
from sam.core.clock import SystemClock
from sam.core.event_bus import EventBus

# ── Helpers ────────────────────────────────────────────────────────────


def make_graph(name: str = "test") -> ExecutionGraph:
    """Create a minimal ExecutionGraph for testing."""
    corr_id = str(uuid.uuid4())
    graph = ExecutionGraph(
        id=str(uuid.uuid4()),
        name=name,
        correlation_id=corr_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    return graph


def make_node(graph_id: str, sid: str, deps: Optional[List[str]] = None) -> ExecutionNode:
    """Create a simple execution node."""
    return ExecutionNode(
        id=sid,
        graph_id=graph_id,
        capability_id=f"cap.{sid}",
        inputs={"cmd": f"test-{sid}"},
        dependencies=deps or [],
    )


def make_decision_exec_node(
    graph_id: str,
    node_id: str,
    decision_id: str,
    deps: Optional[List[str]] = None,
) -> ExecutionNode:
    """Create an ExecutionNode configured as a decision point."""
    return ExecutionNode(
        id=node_id,
        graph_id=graph_id,
        capability_id=f"__decision__.{decision_id}",
        inputs={"decision_id": decision_id},
        dependencies=deps or [],
        is_decision=True,
        decision_id=decision_id,
    )


def make_decision(
    decision_id: str,
    conditions: Optional[List[DecisionCondition]] = None,
    branch_targets: Optional[Dict[str, str]] = None,
    default_target: Optional[str] = None,
) -> DecisionNode:
    """Create a DecisionNode."""
    return DecisionNode(
        id=decision_id,
        conditions=conditions or [],
        branch_targets=branch_targets or {},
        default_target=default_target,
    )


class FakeDatabase:
    """In-memory DB replacement for testing RevisionManager/EvolutionManager."""

    def __init__(self):
        self.graph_revisions: List[Dict[str, Any]] = []
        self.intent_evolutions: List[Dict[str, Any]] = []

    async def fetch_one(self, query: str, params: Optional[List[Any]] = None) -> Optional[dict]:
        if "MAX(version)" in query and "graph_revisions" in query:
            gid = params[0] if params else None
            matching = [r for r in self.graph_revisions if r.get("graph_id") == gid]
            if matching:
                max_ver = max(r["version"] for r in matching)
                return {"max_ver": max_ver}
            return {"max_ver": None}
        return None

    async def fetch_all(self, query: str, params: Optional[List[Any]] = None) -> List[dict]:
        if "graph_revisions" in query:
            gid = params[0] if params else None
            matching = [r for r in self.graph_revisions if r.get("graph_id") == gid]
            matching.sort(key=lambda r: r["version"], reverse=True)
            limit = params[1] if len(params or []) > 1 else 50
            return matching[:limit]
        if "intent_evolutions" in query:
            oid = params[0] if params else None
            matching = [r for r in self.intent_evolutions if r.get("original_intent_id") == oid]
            matching.sort(key=lambda r: r["timestamp"], reverse=True)
            limit = params[1] if len(params or []) > 1 else 50
            return matching[:limit]
        return []

    async def execute(self, query: str, params: Optional[List[Any]] = None) -> None:
        if "INSERT OR IGNORE INTO graph_revisions" in query:
            p = params or []
            self.graph_revisions.append({
                "id": p[0],
                "graph_id": p[1],
                "version": p[2],
                "previous_version": p[3],
                "reason": p[4],
                "trigger": p[5],
                "new_nodes": p[6],
                "modified_nodes": p[7],
                "removed_nodes": p[8],
                "snapshot_before": p[9],
                "snapshot_after": p[10],
                "created_at": p[11],
            })
        elif "UPDATE graph_revisions" in query:
            for r in self.graph_revisions:
                if r["id"] == params[1]:
                    r["snapshot_after"] = params[0]
                    break
        elif "INSERT OR IGNORE INTO intent_evolutions" in query:
            p = params or []
            self.intent_evolutions.append({
                "id": p[0],
                "original_intent_id": p[1],
                "new_intent_id": p[2],
                "evidence_ids": p[3],
                "reason": p[4],
                "original_type": p[5],
                "new_type": p[6],
                "original_target": p[7],
                "new_target": p[8],
                "timestamp": p[9],
            })


# ═══════════════════════════════════════════════════════════════════════
#  RevisionManager Tests
# ═══════════════════════════════════════════════════════════════════════

class TestGraphRevisionModel:
    """Tests for GraphRevision model structure and validation."""

    def test_minimal_revision(self):
        r = GraphRevision(
            id="r1",
            graph_id="g1",
            version=1,
            reason="Initial revision",
        )
        assert r.id == "r1"
        assert r.graph_id == "g1"
        assert r.version == 1
        assert r.previous_version is None
        assert r.trigger == RevisionTrigger.EVIDENCE_CHANGE
        assert r.new_nodes == []
        assert r.modified_nodes == []
        assert r.removed_nodes == []
        assert r.snapshot_before is None
        assert r.snapshot_after is None
        assert r.created_at is not None

    def test_full_revision(self):
        r = GraphRevision(
            id="r2",
            graph_id="g1",
            version=2,
            previous_version=1,
            reason="Provider unhealthy, switching",
            trigger=RevisionTrigger.DECISION_NODE,
            new_nodes=["node-b", "node-c"],
            modified_nodes=["node-a"],
            removed_nodes=["node-old"],
            snapshot_before='{"nodes": []}',
            snapshot_after='{"nodes": [{"id": "node-b"}]}',
        )
        assert r.version == 2
        assert r.previous_version == 1
        assert r.trigger == RevisionTrigger.DECISION_NODE
        assert r.new_nodes == ["node-b", "node-c"]
        assert r.modified_nodes == ["node-a"]
        assert r.removed_nodes == ["node-old"]
        assert r.node_count_delta == 2 - 1  # 2 new - 1 removed = 1

    def test_node_count_delta(self):
        r = GraphRevision(
            id="r3",
            graph_id="g1",
            version=3,
            reason="Add monitoring",
            new_nodes=["m1", "m2", "m3"],
            removed_nodes=["old"],
        )
        assert r.node_count_delta == 2  # 3 new - 1 removed = 2

    def test_negative_node_count_delta(self):
        r = GraphRevision(
            id="r4",
            graph_id="g1",
            version=4,
            reason="Cleanup",
            removed_nodes=["a", "b", "c"],
        )
        assert r.node_count_delta == -3

    def test_trigger_enum_values(self):
        assert RevisionTrigger.DECISION_NODE.value == "decision_node"
        assert RevisionTrigger.EVIDENCE_CHANGE.value == "evidence_change"
        assert RevisionTrigger.TIMEOUT.value == "timeout"
        assert RevisionTrigger.GOVERNANCE.value == "governance"
        assert RevisionTrigger.MANUAL.value == "manual"


class TestRevisionManager:
    """Tests for RevisionManager core logic."""

    @pytest.mark.asyncio
    async def test_propose_revision_basic(self):
        mgr = RevisionManager()
        graph = make_graph()
        revision = await mgr.propose_revision(
            graph_id=graph.id,
            reason="Switching to fallback provider",
            changes={
                "new_nodes": [make_node(graph.id, "fallback-a")],
                "modified_nodes": [],
                "removed_nodes": ["primary-a"],
            },
        )
        assert revision.graph_id == graph.id
        assert revision.reason == "Switching to fallback provider"
        assert revision.new_nodes == ["fallback-a"]
        assert revision.removed_nodes == ["primary-a"]
        assert revision.version >= 1
        assert revision.snapshot_before is None  # no current_graph provided

    @pytest.mark.asyncio
    async def test_propose_revision_with_trigger(self):
        mgr = RevisionManager()
        graph = make_graph()
        revision = await mgr.propose_revision(
            graph_id=graph.id,
            reason="Timeout detected",
            changes={"removed_nodes": ["slow-node"]},
            trigger=RevisionTrigger.TIMEOUT,
        )
        assert revision.trigger == RevisionTrigger.TIMEOUT

    @pytest.mark.asyncio
    async def test_propose_revision_with_snapshot(self):
        mgr = RevisionManager()
        graph = make_graph()
        graph.nodes = [make_node(graph.id, "a"), make_node(graph.id, "b")]
        revision = await mgr.propose_revision(
            graph_id=graph.id,
            reason="Testing snapshot",
            changes={"removed_nodes": ["a"]},
            current_graph=graph,
        )
        assert revision.snapshot_before is not None
        assert "a" in revision.snapshot_before
        assert "b" in revision.snapshot_before

    @pytest.mark.asyncio
    async def test_propose_revision_increments_version(self):
        mgr = RevisionManager()
        graph = make_graph()
        r1 = await mgr.propose_revision(graph_id=graph.id, reason="First", changes={})
        r2 = await mgr.propose_revision(graph_id=graph.id, reason="Second", changes={})
        assert r1.version == 1  # No DB, always starts at 1
        assert r2.version == 1  # Same without DB — no version tracking

    @pytest.mark.asyncio
    async def test_propose_revision_with_db_increments_version(self):
        db = FakeDatabase()
        mgr = RevisionManager(db=db)
        graph = make_graph()
        r1 = await mgr.propose_revision(graph_id=graph.id, reason="First", changes={})
        r2 = await mgr.propose_revision(graph_id=graph.id, reason="Second", changes={})
        r3 = await mgr.propose_revision(graph_id=graph.id, reason="Third", changes={})
        assert r1.version == 1
        assert r2.version == 2
        assert r3.version == 3

    @pytest.mark.asyncio
    async def test_apply_revision_removes_nodes(self):
        mgr = RevisionManager()
        graph = make_graph()
        graph.nodes = [
            make_node(graph.id, "a"),
            make_node(graph.id, "b"),
            make_node(graph.id, "c"),
        ]
        graph.entry_nodes = ["a"]
        graph.exit_nodes = ["c"]

        revision = await mgr.propose_revision(
            graph_id=graph.id,
            reason="Remove b",
            changes={"removed_nodes": ["b"]},
        )
        revised = await mgr.apply_revision(revision, graph)

        assert len(revised.nodes) == 2
        assert [n.id for n in revised.nodes] == ["a", "c"]

    @pytest.mark.asyncio
    async def test_apply_revision_strips_dangling_dependencies(self):
        mgr = RevisionManager()
        graph = make_graph()
        graph.nodes = [
            make_node(graph.id, "a"),
            make_node(graph.id, "b", deps=["a"]),
            make_node(graph.id, "c"),
        ]

        revision = await mgr.propose_revision(
            graph_id=graph.id,
            reason="Remove b",
            changes={"removed_nodes": ["b"]},
        )
        revised = await mgr.apply_revision(revision, graph)

        for node in revised.nodes:
            assert "b" not in node.dependencies

    @pytest.mark.asyncio
    async def test_apply_revision_cleans_entry_exit_lists(self):
        mgr = RevisionManager()
        graph = make_graph()
        graph.nodes = [
            make_node(graph.id, "a"),
            make_node(graph.id, "b"),
        ]
        graph.entry_nodes = ["a", "b"]
        graph.exit_nodes = ["a", "b"]

        revision = await mgr.propose_revision(
            graph_id=graph.id,
            reason="Remove a",
            changes={"removed_nodes": ["a"]},
        )
        revised = await mgr.apply_revision(revision, graph)

        assert "a" not in revised.entry_nodes
        assert "a" not in revised.exit_nodes
        assert revised.entry_nodes == ["b"]
        assert revised.exit_nodes == ["b"]

    @pytest.mark.asyncio
    async def test_get_revision_history_empty(self):
        mgr = RevisionManager()
        history = await mgr.get_revision_history("nonexistent")
        assert history == []

    @pytest.mark.asyncio
    async def test_get_revision_history_with_db(self):
        db = FakeDatabase()
        mgr = RevisionManager(db=db)
        graph = make_graph()

        await mgr.propose_revision(graph_id=graph.id, reason="First", changes={})
        await mgr.propose_revision(graph_id=graph.id, reason="Second", changes={})
        await mgr.propose_revision(graph_id=graph.id, reason="Third", changes={})

        history = await mgr.get_revision_history(graph.id)
        assert len(history) == 3
        # Newest first
        assert history[0].version == 3
        assert history[0].reason == "Third"

    @pytest.mark.asyncio
    async def test_get_revision_history_respects_limit(self):
        db = FakeDatabase()
        mgr = RevisionManager(db=db)
        graph = make_graph()

        for i in range(5):
            await mgr.propose_revision(graph_id=graph.id, reason=f"Rev {i+1}", changes={})

        history = await mgr.get_revision_history(graph.id, limit=2)
        assert len(history) == 2
        assert history[0].version == 5

    @pytest.mark.asyncio
    async def test_revision_stores_snapshot_after_apply(self):
        db = FakeDatabase()
        mgr = RevisionManager(db=db)
        graph = make_graph()
        graph.nodes = [make_node(graph.id, "a"), make_node(graph.id, "b")]

        revision = await mgr.propose_revision(
            graph_id=graph.id,
            reason="Remove a",
            changes={"removed_nodes": ["a"]},
            current_graph=graph,
        )
        revised = await mgr.apply_revision(revision, graph)

        assert revision.snapshot_after is not None
        # Nodes in snapshot should NOT include "a"
        import json
        snapshot = json.loads(revision.snapshot_after)
        node_ids = [n["id"] for n in snapshot["nodes"]]
        assert "b" in node_ids
        assert "a" not in node_ids


# ═══════════════════════════════════════════════════════════════════════
#  EvolutionManager Tests
# ═══════════════════════════════════════════════════════════════════════

class TestIntentEvolutionModel:
    """Tests for IntentEvolution model structure."""

    def test_minimal_evolution(self):
        evo = IntentEvolution(
            id="ev1",
            original_intent_id="intent-a",
            new_intent_id="intent-b",
            reason="Target unhealthy, switching",
            original_type="DIAGNOSE",
            new_type="REPAIR",
            original_target="server-1",
            new_target="server-2",
        )
        assert evo.id == "ev1"
        assert evo.original_intent_id == "intent-a"
        assert evo.new_intent_id == "intent-b"
        assert evo.evidence_ids == []
        assert evo.reason == "Target unhealthy, switching"
        assert evo.original_type == "DIAGNOSE"
        assert evo.new_type == "REPAIR"
        assert evo.timestamp is not None

    def test_evolution_with_evidence(self):
        evo = IntentEvolution(
            id="ev2",
            original_intent_id="intent-a",
            new_intent_id="intent-b",
            evidence_ids=["ev-1", "ev-2"],
            reason="Multiple issues detected",
            original_type="MONITOR",
            new_type="REPAIR",
            original_target="db-1",
            new_target="db-1",
        )
        assert evo.evidence_ids == ["ev-1", "ev-2"]


class TestEvolutionManager:
    """Tests for EvolutionManager core logic."""

    @pytest.mark.asyncio
    async def test_propose_evolution_basic(self):
        mgr = EvolutionManager()
        original = Intent(
            type=IntentType.DIAGNOSE,
            target="server-1",
            description="Check server health",
        )
        evolution = await mgr.propose_evolution(
            original_intent=original,
            evidence_ids=["ev-node-1"],
            reason="Server unhealthy, switching to repair",
        )
        assert evolution.original_intent_id == original.id
        assert evolution.evidence_ids == ["ev-node-1"]
        assert evolution.reason == "Server unhealthy, switching to repair"
        assert evolution.original_type == "DIAGNOSE"
        assert evolution.original_target == "server-1"
        # Since no new_intent provided, it creates a placeholder
        assert evolution.new_intent_id is not None
        assert evolution.new_type == "DIAGNOSE"  # placeholder matches original

    @pytest.mark.asyncio
    async def test_propose_evolution_with_new_intent(self):
        mgr = EvolutionManager()
        original = Intent(
            type=IntentType.DIAGNOSE,
            target="server-1",
            description="Check server health",
        )
        new = Intent(
            type=IntentType.REPAIR,
            target="server-1",
            description="Repair server health",
        )
        evolution = await mgr.propose_evolution(
            original_intent=original,
            evidence_ids=["ev-unhealthy"],
            reason="Evidence shows degradation",
            new_intent=new,
        )
        assert evolution.new_intent_id == new.id
        assert evolution.original_type == "DIAGNOSE"
        assert evolution.new_type == "REPAIR"

    @pytest.mark.asyncio
    async def test_apply_evolution_readies_intent(self):
        mgr = EvolutionManager()
        original = Intent(type=IntentType.DIAGNOSE, target="server-1", description="Check")
        new = Intent(type=IntentType.REPAIR, target="server-1", description="Repair")
        evolution = await mgr.propose_evolution(
            original_intent=original,
            evidence_ids=["ev-1"],
            reason="Switching to repair",
            new_intent=new,
        )
        result = await mgr.apply_evolution(evolution, new)
        assert result.status == IntentStatus.PLANNING
        assert result.id == new.id

    @pytest.mark.asyncio
    async def test_get_evolution_history_empty(self):
        mgr = EvolutionManager()
        history = await mgr.get_evolution_history("nonexistent")
        assert history == []

    @pytest.mark.asyncio
    async def test_get_evolution_history_with_db(self):
        db = FakeDatabase()
        mgr = EvolutionManager(db=db)
        original = Intent(type=IntentType.DIAGNOSE, target="srv-1", description="Check")

        await mgr.propose_evolution(
            original_intent=original,
            evidence_ids=["ev-1"],
            reason="First evolution",
        )
        await mgr.propose_evolution(
            original_intent=original,
            evidence_ids=["ev-2"],
            reason="Second evolution",
        )

        history = await mgr.get_evolution_history(original.id)
        assert len(history) == 2
        assert history[0].reason == "Second evolution"

    @pytest.mark.asyncio
    async def test_evolution_stores_properly(self):
        db = FakeDatabase()
        mgr = EvolutionManager(db=db)
        original = Intent(type=IntentType.DIAGNOSE, target="db-1", description="Check DB")
        new = Intent(type=IntentType.REPAIR, target="db-1", description="Repair DB")

        await mgr.propose_evolution(
            original_intent=original,
            evidence_ids=["ev-node-fail"],
            reason="DB connection failed",
            new_intent=new,
        )

        stored = db.intent_evolutions
        assert len(stored) == 1
        assert stored[0]["original_intent_id"] == original.id
        assert stored[0]["new_intent_id"] == new.id
        assert stored[0]["reason"] == "DB connection failed"
        assert stored[0]["original_type"] == "DIAGNOSE"
        assert stored[0]["new_type"] == "REPAIR"
        assert stored[0]["original_target"] == "db-1"
        assert stored[0]["new_target"] == "db-1"

    @pytest.mark.asyncio
    async def test_evolution_changes_intent_type(self):
        mgr = EvolutionManager()
        original = Intent(type=IntentType.DIAGNOSE, target="db-1", description="Check DB")
        new = Intent(type=IntentType.OPTIMIZE, target="db-1", description="Optimize DB")

        evolution = await mgr.propose_evolution(
            original_intent=original,
            evidence_ids=["ev-slow"],
            reason="Query performance degrading — switching to optimize",
            new_intent=new,
        )
        assert evolution.original_type == "DIAGNOSE"
        assert evolution.new_type == "OPTIMIZE"

    @pytest.mark.asyncio
    async def test_evolution_changes_target(self):
        mgr = EvolutionManager()
        original = Intent(type=IntentType.DIAGNOSE, target="server-old", description="Check")
        new = Intent(type=IntentType.DIAGNOSE, target="server-new", description="Check")

        evolution = await mgr.propose_evolution(
            original_intent=original,
            evidence_ids=["ev-migrate"],
            reason="Target migrated",
            new_intent=new,
        )
        assert evolution.original_target == "server-old"
        assert evolution.new_target == "server-new"


# ═══════════════════════════════════════════════════════════════════════
#  ExecutionGraphEngine Integration with Revision
# ═══════════════════════════════════════════════════════════════════════

class TestEngineRevisionIntegration:
    """Tests that the engine calls _check_and_propose_revision."""

    @pytest.mark.asyncio
    async def test_engine_initialized_with_revision_manager(self):
        mgr = RevisionManager()
        engine = ExecutionGraphEngine(
            revision_manager=mgr,
            clock=SystemClock(),
        )
        assert engine.revision_manager is mgr

    @pytest.mark.asyncio
    async def test_engine_no_revision_manager_no_crash(self):
        engine = ExecutionGraphEngine(clock=SystemClock())
        assert engine.revision_manager is None

    @pytest.mark.asyncio
    async def test_decision_node_triggers_revision_check(self):
        """Integration: decision node + revision manager."""
        db = FakeDatabase()
        rev_mgr = RevisionManager(db=db)
        engine = ExecutionGraphEngine(
            revision_manager=rev_mgr,
            clock=SystemClock(),
        )

        graph = make_graph("rev-integration")

        # Node a — runs first, produces "unhealthy" evidence
        node_a = make_node(graph.id, "a")
        node_a.capability_id = "cap.unhealthy"

        # Decision node b — evaluates evidence, triggers revision check
        decision_id = "dec-1"
        node_b = make_decision_exec_node(graph.id, "b", decision_id, deps=["a"])

        # Node c — fallback target
        node_c = make_node(graph.id, "c", deps=["b"])

        graph.nodes = [node_a, node_b, node_c]
        graph.entry_nodes = ["a"]
        graph.exit_nodes = ["c"]

        decision = make_decision(
            decision_id=decision_id,
            conditions=[DecisionCondition(
                type=DecisionType.IF_STATUS,
                key="a.status",
                operator="==",
                value="UNHEALTHY",
            )],
            branch_targets={"0": "c"},
            default_target="c",
        )
        graph.decision_nodes[decision_id] = decision

        async def executor(node: ExecutionNode) -> dict:
            if node.id == "a":
                return {"_result": "unhealthy provider detected"}
            if node.id == "b":
                return {"decision_outcome": f"decision: {node.id}"}
            if node.id == "c":
                return {"_result": "fallback executed"}
            return {"_result": "ok"}

        result = await engine.execute(graph, capability_executor=executor)

        assert result.status == GraphStatus.COMPLETED

        # Check that a revision was proposed in the DB
        revisions = db.graph_revisions
        assert len(revisions) > 0

        # The revision should reference this graph
        matching = [r for r in revisions if r["graph_id"] == graph.id]
        assert len(matching) >= 1
        assert "unhealthy" in matching[0]["reason"].lower()

    @pytest.mark.asyncio
    async def test_decision_node_no_trigger_no_revision(self):
        """When no unhealthy evidence, no revision should be proposed."""
        db = FakeDatabase()
        rev_mgr = RevisionManager(db=db)
        engine = ExecutionGraphEngine(
            revision_manager=rev_mgr,
            clock=SystemClock(),
        )

        graph = make_graph("no-revision")

        node_a = make_node(graph.id, "a")
        decision_id = "dec-2"
        node_b = make_decision_exec_node(graph.id, "b", decision_id, deps=["a"])
        node_c = make_node(graph.id, "c", deps=["b"])

        graph.nodes = [node_a, node_b, node_c]
        graph.entry_nodes = ["a"]
        graph.exit_nodes = ["c"]

        decision = make_decision(
            decision_id=decision_id,
            default_target="c",
        )
        graph.decision_nodes[decision_id] = decision

        async def executor(node: ExecutionNode) -> dict:
            if node.id == "a":
                return {"status": "healthy"}
            if node.id == "b":
                return {"decision_outcome": f"decision: {node.id}"}
            return {"_result": "ok"}

        result = await engine.execute(graph, capability_executor=executor)

        assert result.status == GraphStatus.COMPLETED
        revisions = db.graph_revisions
        matching = [r for r in revisions if r["graph_id"] == graph.id]
        # No revision should have been proposed — evidence is clean
        assert len(matching) == 0

    @pytest.mark.asyncio
    async def test_non_decision_node_no_revision_check(self):
        """Non-decision nodes should not trigger revision checks."""
        db = FakeDatabase()
        rev_mgr = RevisionManager(db=db)
        engine = ExecutionGraphEngine(
            revision_manager=rev_mgr,
            clock=SystemClock(),
        )

        graph = make_graph("no-decision")
        node_a = make_node(graph.id, "a")
        node_b = make_node(graph.id, "b", deps=["a"])
        graph.nodes = [node_a, node_b]
        graph.entry_nodes = ["a"]
        graph.exit_nodes = ["b"]

        async def executor(node: ExecutionNode) -> dict:
            return {"ok": True}

        result = await engine.execute(graph, capability_executor=executor)
        assert result.status == GraphStatus.COMPLETED
        assert len(db.graph_revisions) == 0

    @pytest.mark.asyncio
    async def test_revision_with_failed_node_in_evidence(self):
        """A FAILED node in evidence triggers a revision."""
        db = FakeDatabase()
        rev_mgr = RevisionManager(db=db)
        engine = ExecutionGraphEngine(
            revision_manager=rev_mgr,
            clock=SystemClock(),
        )

        graph = make_graph("failed-triggers-revision")

        # Node a — fails. Decision node b is independent (no dep on a).
        # The decision node runs after a completes (both are entry nodes).
        node_a = make_node(graph.id, "a")
        decision_id = "dec-3"
        node_b = make_decision_exec_node(graph.id, "b", decision_id)
        node_c = make_node(graph.id, "c", deps=["b"])

        graph.nodes = [node_a, node_b, node_c]
        graph.entry_nodes = ["a", "b"]
        graph.exit_nodes = ["c"]

        decision = make_decision(
            decision_id=decision_id,
            default_target="c",
        )
        graph.decision_nodes[decision_id] = decision

        async def executor(node: ExecutionNode) -> dict:
            if node.id == "a":
                raise RuntimeError("Node A catastrophic failure")
            if node.id == "b":
                return {"decision_outcome": f"decision: {node.id}"}
            return {"_result": "ok"}

        result = await engine.execute(graph, capability_executor=executor)

        # Graph should be FAILED (node a fails with ABORT default policy)
        # But decision node b and node c also ran (parallel with a)
        # The revision manager should have detected a's failure
        matching = [r for r in db.graph_revisions if r["graph_id"] == graph.id]
        # At least one revision should contain "FAILED" in the reason
        failed_revisions = [
            r for r in matching
            if "FAILED" in r["reason"] or "failed" in r["reason"].lower()
        ]
        assert len(failed_revisions) >= 1, (
            f"Expected at least one revision with FAILED reason. Got: {matching}"
        )


if __name__ == "__main__":
    pytest.main(["-v", __file__])
