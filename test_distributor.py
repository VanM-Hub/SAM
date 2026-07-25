"""
Tests for ClusterDistributor (distributor.py)
Pattern: inline replica classes + _TestDB shim, pytest-asyncio.
"""

from __future__ import annotations

import sqlite3
import pytest
from datetime import datetime

# Minimal inline replicas for Node, Job, JobRecord, NodeRegistry, JobQueue

class NodeStatus:
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class NodeCapabilities:
    SCHEDULER = "SCHEDULER"
    WORKER = "WORKER"


class RuntimeNode:
    def __init__(self, node_id: str, labels=None, capabilities=None, status=NodeStatus.ONLINE):
        self.node_id = node_id
        self.labels = labels or {}
        self.capabilities = capabilities or []
        self.status = status

    def has_capability(self, cap):
        return cap in self.capabilities


class Job:
    def __init__(self, id: str, payload: dict = None):
        self.id = id
        self.payload = payload or {}


class JobRecord:
    def __init__(self, job: Job, status: str = "PENDING"):
        self.job = job
        self.status = status


class _LeaderElection:
    def __init__(self, leader=True):
        self._leader = leader

    async def is_leader(self, node_id: str) -> bool:
        return self._leader


class _NodeRegistry:
    def __init__(self, nodes: list):
        self._nodes = nodes

    async def list(self, status=None):
        if status is None:
            return self._nodes
        return [n for n in self._nodes if n.status == status]


class _JobQueue:
    def __init__(self, jobs: list):
        self._jobs = jobs

    async def list_pending(self):
        return [JobRecord(j, status="PENDING") for j in self._jobs]


# _TestDB shim similar to test_leader pattern
class _TestDB:
    def __init__(self):
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self._conn.execute(
            "CREATE TABLE job_assignments ("
            "job_id TEXT NOT NULL PRIMARY KEY,"
            "assigned_node_id TEXT NOT NULL,"
            "assigned_at TEXT NOT NULL,"
            "status TEXT NOT NULL DEFAULT 'PENDING',"
            "attempts INTEGER NOT NULL DEFAULT 0,"
            "error TEXT,"
            "completed_at TEXT"
            ")"
        )
        self._conn.execute(
            "CREATE TABLE workflow_assignments ("
            "workflow_id TEXT NOT NULL PRIMARY KEY,"
            "assigned_node_id TEXT NOT NULL,"
            "assigned_at TEXT NOT NULL,"
            "status TEXT NOT NULL DEFAULT 'PENDING',"
            "attempts INTEGER NOT NULL DEFAULT 0,"
            "error TEXT,"
            "completed_at TEXT"
            ")"
        )
        self._conn.commit()

    async def execute(self, sql, params=None):
        cur = self._conn.cursor()
        cur.execute(sql, params or [])
        self._conn.commit()
        return cur

    async def fetch_one(self, sql, params=None):
        cur = self._conn.cursor()
        cur.execute(sql, params or [])
        return cur.fetchone()

    async def fetch_all(self, sql, params=None):
        cur = self._conn.cursor()
        cur.execute(sql, params or [])
        return cur.fetchall()

    def close(self):
        self._conn.close()


# Import the ClusterDistributor from production code
from src.sam.cluster.distributor import ClusterDistributor, AssignmentStrategy, NoSuitableNodeError, NotLeaderError


@pytest.fixture
def db():
    _db = _TestDB()
    yield _db
    _db.close()


@pytest.mark.asyncio
async def test_round_robin_assignment(db):
    nodes = [RuntimeNode(f"node-{i}") for i in range(3)]
    registry = _NodeRegistry(nodes)
    jobs = [Job(f"job-{i}") for i in range(3)]
    queue = _JobQueue(jobs)
    leader = _LeaderElection(leader=True)

    dist = ClusterDistributor(registry, queue, leader, db, strategy=AssignmentStrategy.ROUND_ROBIN, node_id="node-0")
    count = await dist.distribute_jobs()
    assert count == 3

    rows = await db.fetch_all("SELECT job_id, assigned_node_id FROM job_assignments ORDER BY job_id")
    assigned = [dict(r)["assigned_node_id"] for r in rows]
    # Round robin across node-0, node-1, node-2
    assert assigned == ["node-0", "node-1", "node-2"]


@pytest.mark.asyncio
async def test_least_loaded_assignment(db):
    # Pre-insert assignments to make node-0 heavier
    await db.execute("INSERT INTO job_assignments (job_id, assigned_node_id, assigned_at, status, attempts) VALUES (?, ?, ?, ?, 0)", ["existing-1", "node-0", datetime.utcnow().isoformat(), "ASSIGNED"])

    nodes = [RuntimeNode("node-0"), RuntimeNode("node-1")]
    registry = _NodeRegistry(nodes)
    jobs = [Job("job-A"), Job("job-B")]
    queue = _JobQueue(jobs)
    leader = _LeaderElection(leader=True)

    dist = ClusterDistributor(registry, queue, leader, db, strategy=AssignmentStrategy.LEAST_LOADED, node_id="node-0")
    count = await dist.distribute_jobs()
    assert count == 2

    rows = await db.fetch_all("SELECT job_id, assigned_node_id FROM job_assignments ORDER BY job_id")
    mapping = {dict(r)["job_id"]: dict(r)["assigned_node_id"] for r in rows}
    # existing-1 stays on node-0; new jobs should prefer node-1 (less loaded)
    assert mapping["job-A"] == "node-1"
    assert mapping["job-B"] == "node-1"


@pytest.mark.asyncio
async def test_capability_aware_assignment(db):
    nodes = [RuntimeNode("n1", capabilities=[NodeCapabilities.WORKER]), RuntimeNode("n2", capabilities=[NodeCapabilities.SCHEDULER, NodeCapabilities.WORKER])]
    registry = _NodeRegistry(nodes)
    # Job requires SCHEDULER
    jobs = [Job("j1", payload={"required_capability": "SCHEDULER"})]
    queue = _JobQueue(jobs)
    leader = _LeaderElection(leader=True)

    dist = ClusterDistributor(registry, queue, leader, db, strategy=AssignmentStrategy.CAPABILITY_AWARE, node_id="n2")
    count = await dist.distribute_jobs()
    assert count == 1

    row = await db.fetch_one("SELECT assigned_node_id FROM job_assignments WHERE job_id=?", ["j1"])
    assert dict(row)["assigned_node_id"] == "n2"


@pytest.mark.asyncio
async def test_affinity_assignment(db):
    nodes = [RuntimeNode("n-a", labels={"zone": "us-east"}), RuntimeNode("n-b", labels={"zone": "us-west"})]
    registry = _NodeRegistry(nodes)
    jobs = [Job("ja", payload={"node_selector": {"zone": "us-west"}})]
    queue = _JobQueue(jobs)
    leader = _LeaderElection(leader=True)

    dist = ClusterDistributor(registry, queue, leader, db, strategy=AssignmentStrategy.AFFINITY, node_id="n-a")
    count = await dist.distribute_jobs()
    assert count == 1

    row = await db.fetch_one("SELECT assigned_node_id FROM job_assignments WHERE job_id=?", ["ja"])
    assert dict(row)["assigned_node_id"] == "n-b"


@pytest.mark.asyncio
async def test_distribute_workflows(db):
    nodes = [RuntimeNode("s1", capabilities=[NodeCapabilities.SCHEDULER]), RuntimeNode("s2", capabilities=[NodeCapabilities.WORKER])]
    registry = _NodeRegistry(nodes)
    queue = _JobQueue([])
    leader = _LeaderElection(leader=True)

    dist = ClusterDistributor(registry, queue, leader, db, strategy=AssignmentStrategy.LEAST_LOADED, node_id="s1")
    count = await dist.distribute_workflows(["wf-1", "wf-2"])
    assert count == 2

    rows = await db.fetch_all("SELECT workflow_id, assigned_node_id FROM workflow_assignments ORDER BY workflow_id")
    assigned = [dict(r)["assigned_node_id"] for r in rows]
    # Only s1 has SCHEDULER capability; both workflows go to s1
    assert assigned == ["s1", "s1"]


@pytest.mark.asyncio
async def test_get_assignments_and_filter(db):
    nodes = [RuntimeNode("n1")]
    registry = _NodeRegistry(nodes)
    jobs = [Job("x1"), Job("x2")]
    queue = _JobQueue(jobs)
    leader = _LeaderElection(leader=True)

    dist = ClusterDistributor(registry, queue, leader, db, strategy=AssignmentStrategy.ROUND_ROBIN, node_id="n1")
    await dist.distribute_jobs()

    all_assigns = await dist.get_assignments()
    assert len(all_assigns) == 2

    assigned_only = await dist.get_assignments(status=None)
    assert len(assigned_only) == 2


@pytest.mark.asyncio
async def test_not_leader_raises(db):
    nodes = [RuntimeNode("n1")]
    registry = _NodeRegistry(nodes)
    jobs = [Job("z1")]
    queue = _JobQueue(jobs)
    leader = _LeaderElection(leader=False)

    dist = ClusterDistributor(registry, queue, leader, db, strategy=AssignmentStrategy.ROUND_ROBIN, node_id="n1")
    with pytest.raises(NotLeaderError):
        await dist.distribute_jobs()


@pytest.mark.asyncio
async def test_assign_existing_updates_attempts(db):
    nodes = [RuntimeNode("n1")]
    registry = _NodeRegistry(nodes)
    jobs = [Job("dup")]
    queue = _JobQueue(jobs)
    leader = _LeaderElection(leader=True)

    dist = ClusterDistributor(registry, queue, leader, db, strategy=AssignmentStrategy.ROUND_ROBIN, node_id="n1")
    # First assign
    await dist.distribute_jobs()
    row1 = await db.fetch_one("SELECT attempts FROM job_assignments WHERE job_id=?", ["dup"])
    assert dict(row1)["attempts"] == 0

    # Assign again (simulate retry)
    await dist.assign_job("dup", "n1")
    row2 = await db.fetch_one("SELECT attempts FROM job_assignments WHERE job_id=?", ["dup"])
    assert dict(row2)["attempts"] == 1


@pytest.mark.asyncio
async def test_select_node_no_nodes(db):
    # Node registry empty
    registry = _NodeRegistry([])
    jobs = [Job("j-none")]
    queue = _JobQueue(jobs)
    leader = _LeaderElection(leader=True)

    dist = ClusterDistributor(registry, queue, leader, db, strategy=AssignmentStrategy.ROUND_ROBIN, node_id="n")
    with pytest.raises(NoSuitableNodeError):
        await dist.select_node(jobs[0])
