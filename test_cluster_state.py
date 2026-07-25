"""
Tests for ClusterStateAggregator (state.py)
Pattern: inline replica classes + mock components, pytest-asyncio.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta

from src.sam.cluster.state import ClusterState, ClusterStateAggregator


# ── Inline Replicas ───────────────────────────────────────────────────


class NodeStatus:
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"


class RuntimeNode:
    def __init__(
        self,
        node_id: str,
        status=NodeStatus.ONLINE,
        hostname: str = "",
        version: str = "1.0.0",
        capabilities=None,
        health=None,
    ):
        self.node_id = node_id
        self.status = status
        self.hostname = hostname or f"{node_id}.local"
        self.version = version
        self.capabilities = capabilities or []
        self.health = health or {}


class _LeaderRecord:
    def __init__(self, leader_id: str, cluster_id: str = "test-cluster"):
        self.leader_id = leader_id
        self.cluster_id = cluster_id


class _NodeRegistry:
    def __init__(self, nodes=None):
        self._nodes = nodes or []

    async def list(self, status=None):
        if status is None:
            return self._nodes
        return [n for n in self._nodes if n.status == status]


class _JobQueue:
    def __init__(self, stats=None):
        self._stats = stats or {"pending": 0, "running": 0, "failed": 0, "total": 0}

    async def stats(self):
        return self._stats


class _LeaderElection:
    def __init__(self, leader_id=None, raise_on_get=False):
        self._leader_id = leader_id
        self._raise_on_get = raise_on_get

    async def get_leader(self):
        if self._raise_on_get:
            raise RuntimeError("DB error")
        if self._leader_id is None:
            return None
        return _LeaderRecord(leader_id=self._leader_id)


# ── Fixture ───────────────────────────────────────────────────────────


@pytest.fixture
def aggregator():
    """Basic aggregator with empty registries."""
    node_reg = _NodeRegistry([])
    job_q = _JobQueue()
    leader_el = _LeaderElection()
    return ClusterStateAggregator(
        node_registry=node_reg,
        job_queue=job_q,
        leader_election=leader_el,
    )


# ── 1. ClusterState Model Tests ───────────────────────────────────────


def test_cluster_state_creation():
    state = ClusterState(cluster_id="test-cluster")
    assert state.cluster_id == "test-cluster"
    assert state.node_count == 0
    assert state.online_nodes == 0
    assert state.offline_nodes == 0
    assert state.degraded_nodes == 0
    assert state.pending_jobs == 0
    assert state.running_jobs == 0
    assert state.failed_jobs == 0
    assert state.total_load == 0.0
    assert state.leader_id is None
    assert isinstance(state.updated_at, datetime)


def test_cluster_state_full():
    state = ClusterState(
        cluster_id="prod",
        node_count=5,
        online_nodes=4,
        offline_nodes=1,
        degraded_nodes=0,
        active_workflows=3,
        pending_jobs=10,
        running_jobs=5,
        failed_jobs=2,
        total_load=45.5,
        leader_id="node-1",
        node_details={"node-1": {"load": 30.0}},
    )
    assert state.cluster_id == "prod"
    assert state.node_count == 5
    assert state.online_nodes == 4
    assert state.offline_nodes == 1
    assert state.total_load == 45.5


def test_cluster_state_to_dict():
    state = ClusterState(
        cluster_id="prod",
        node_count=2,
        online_nodes=2,
        pending_jobs=3,
        running_jobs=1,
        leader_id="node-A",
    )
    d = state.to_dict()
    assert d["cluster_id"] == "prod"
    assert d["node_count"] == 2
    assert d["online_nodes"] == 2
    assert d["pending_jobs"] == 3
    assert d["running_jobs"] == 1
    assert d["leader_id"] == "node-A"
    assert "updated_at" in d


def test_cluster_state_to_summary():
    state = ClusterState(
        cluster_id="prod",
        node_count=5,
        online_nodes=4,
        pending_jobs=10,
        running_jobs=5,
        failed_jobs=2,
        leader_id="node-1",
    )
    summary = state.to_summary()
    assert summary["cluster_id"] == "prod"
    assert "4/5" in summary["nodes"]
    assert "P:10 R:5 F:2" in summary["jobs"]
    assert summary["leader"] == "node-1"


def test_cluster_state_repr():
    state = ClusterState(
        cluster_id="prod",
        node_count=3,
        online_nodes=3,
        pending_jobs=5,
        running_jobs=2,
        total_load=30.0,
        leader_id="n1",
    )
    r = repr(state)
    assert "prod" in r
    assert "3/3" in r
    assert "P:5/R:2" in r
    assert "30.0%" in r
    assert "n1" in r


# ── 2. collect() Tests ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_collect_empty_cluster():
    """Collect should return zeros for empty cluster."""
    node_reg = _NodeRegistry([])
    job_q = _JobQueue()
    leader_el = _LeaderElection()
    agg = ClusterStateAggregator(node_reg, job_q, leader_el)

    state = await agg.collect()
    assert state.cluster_id == "default-cluster"
    assert state.node_count == 0
    assert state.online_nodes == 0
    assert state.pending_jobs == 0
    assert state.running_jobs == 0
    assert state.failed_jobs == 0
    assert state.leader_id is None


@pytest.mark.asyncio
async def test_collect_with_nodes():
    """Collect should count nodes by status."""
    nodes = [
        RuntimeNode("n1", status=NodeStatus.ONLINE),
        RuntimeNode("n2", status=NodeStatus.ONLINE),
        RuntimeNode("n3", status=NodeStatus.OFFLINE),
        RuntimeNode("n4", status=NodeStatus.DEGRADED),
    ]
    node_reg = _NodeRegistry(nodes)
    job_q = _JobQueue()
    leader_el = _LeaderElection()
    agg = ClusterStateAggregator(node_reg, job_q, leader_el)

    state = await agg.collect()
    assert state.node_count == 4
    assert state.online_nodes == 2
    assert state.offline_nodes == 1
    assert state.degraded_nodes == 1


@pytest.mark.asyncio
async def test_collect_with_jobs():
    """Collect should include job stats."""
    node_reg = _NodeRegistry([])
    job_q = _JobQueue({"pending": 7, "running": 3, "failed": 1, "total": 11})
    leader_el = _LeaderElection()
    agg = ClusterStateAggregator(node_reg, job_q, leader_el)

    state = await agg.collect()
    assert state.pending_jobs == 7
    assert state.running_jobs == 3
    assert state.failed_jobs == 1


@pytest.mark.asyncio
async def test_collect_with_leader():
    """Collect should capture leader_id."""
    node_reg = _NodeRegistry([
        RuntimeNode("leader-node", status=NodeStatus.ONLINE),
    ])
    job_q = _JobQueue()
    leader_el = _LeaderElection(leader_id="leader-node")
    agg = ClusterStateAggregator(node_reg, job_q, leader_el)

    state = await agg.collect()
    assert state.leader_id == "leader-node"


@pytest.mark.asyncio
async def test_collect_leader_query_error():
    """Collect should handle leader query errors gracefully (leader_id=None)."""
    node_reg = _NodeRegistry([
        RuntimeNode("n1", status=NodeStatus.ONLINE),
    ])
    job_q = _JobQueue()
    leader_el = _LeaderElection(raise_on_get=True)
    agg = ClusterStateAggregator(node_reg, job_q, leader_el)

    state = await agg.collect()
    assert state.leader_id is None
    assert state.node_count == 1


@pytest.mark.asyncio
async def test_collect_node_details():
    """Collect should populate node_details dict per node."""
    nodes = [
        RuntimeNode(
            "n1",
            status=NodeStatus.ONLINE,
            hostname="node-one.local",
            version="2.0.1",
            capabilities=["WORKER"],
            health={"load": 25.0},
        ),
        RuntimeNode(
            "n2",
            status=NodeStatus.OFFLINE,
            hostname="node-two.local",
        ),
    ]
    node_reg = _NodeRegistry(nodes)
    job_q = _JobQueue()
    leader_el = _LeaderElection()
    agg = ClusterStateAggregator(node_reg, job_q, leader_el)

    state = await agg.collect()
    assert len(state.node_details) == 2
    assert state.node_details["n1"]["status"] == "ONLINE"
    assert state.node_details["n1"]["hostname"] == "node-one.local"
    assert state.node_details["n1"]["version"] == "2.0.1"
    assert state.node_details["n1"]["load"] == 25.0
    assert state.node_details["n2"]["status"] == "OFFLINE"


# ── 3. get_summary() Tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_summary():
    """get_summary should return a quick dict snapshot."""
    nodes = [
        RuntimeNode("n1", status=NodeStatus.ONLINE, hostname="alpha"),
        RuntimeNode("n2", status=NodeStatus.ONLINE, hostname="beta"),
    ]
    node_reg = _NodeRegistry(nodes)
    job_q = _JobQueue({"pending": 2, "running": 1, "failed": 0, "total": 3})
    leader_el = _LeaderElection(leader_id="n1")
    agg = ClusterStateAggregator(node_reg, job_q, leader_el)

    summary = await agg.get_summary()
    assert summary["cluster_id"] == "default-cluster"
    assert "2/2" in summary["nodes"]
    assert "P:2 R:1" in summary["jobs"]
    assert summary["leader"] == "n1"


# ── 4. Load Calculation Tests ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_load_calculation_no_nodes():
    """Load should be 0 when no nodes online."""
    node_reg = _NodeRegistry([])
    job_q = _JobQueue({"pending": 10, "running": 5, "failed": 0, "total": 15})
    leader_el = _LeaderElection()
    agg = ClusterStateAggregator(node_reg, job_q, leader_el)

    state = await agg.collect()
    assert state.total_load == 0.0


@pytest.mark.asyncio
async def test_load_calculation_low():
    """Low load scenario: few jobs, many nodes."""
    nodes = [
        RuntimeNode("n1", health={"load": 10.0}),
        RuntimeNode("n2", health={"load": 5.0}),
        RuntimeNode("n3", health={"load": 8.0}),
    ]
    node_reg = _NodeRegistry(nodes)
    job_q = _JobQueue({"pending": 1, "running": 0, "failed": 0, "total": 1})
    leader_el = _LeaderElection()
    agg = ClusterStateAggregator(node_reg, job_q, leader_el)

    state = await agg.collect()
    # Average node load: (10+5+8)/3 ≈ 7.67
    # Job pressure: (1+0)/(3*5) = 1/15 = 0.0667
    # Combined: 7.67*0.6 + 0.0667*40 = ~7.27
    assert 5.0 <= state.total_load <= 15.0


@pytest.mark.asyncio
async def test_load_calculation_high():
    """High load scenario: many jobs, few nodes."""
    nodes = [
        RuntimeNode("n1", health={"load": 80.0}),
    ]
    node_reg = _NodeRegistry(nodes)
    job_q = _JobQueue({"pending": 20, "running": 5, "failed": 0, "total": 25})
    leader_el = _LeaderElection()
    agg = ClusterStateAggregator(node_reg, job_q, leader_el)

    state = await agg.collect()
    # Average node load: 80.0
    # Job pressure: (20+5)/(1*5) = 25/5 = 5.0 → capped to 1.0
    # Combined: 80*0.6 + 1.0*40 = 48 + 40 = 88.0
    assert 80.0 <= state.total_load <= 100.0


# ── 5. Idempotency / Repeated Collection ──────────────────────────────


@pytest.mark.asyncio
async def test_collect_multiple_times():
    """Multiple collect calls should all succeed."""
    nodes = [
        RuntimeNode("n1", status=NodeStatus.ONLINE),
        RuntimeNode("n2", status=NodeStatus.ONLINE),
    ]
    node_reg = _NodeRegistry(nodes)
    job_q = _JobQueue({"pending": 1, "running": 2, "failed": 0, "total": 3})
    leader_el = _LeaderElection(leader_id="n1")
    agg = ClusterStateAggregator(node_reg, job_q, leader_el)

    # Collect 3 times
    for _ in range(3):
        state = await agg.collect()
        assert state.node_count == 2
        assert state.online_nodes == 2
        assert state.pending_jobs == 1
        assert state.running_jobs == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
