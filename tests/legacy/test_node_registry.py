"""
Tests for Node Registry — Runtime Node & Cluster Identity.
Uses inline replica classes + _TestDB shim (same pattern as checkpoint tests).
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytest

# ── Inline replica of cluster/node.py ────────────────────────────────


class _NodeStatus:
    INITIALIZING = "INITIALIZING"
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    UNHEALTHY = "UNHEALTHY"


class _NodeCapabilities:
    SCHEDULER = "SCHEDULER"
    WORKER = "WORKER"
    PLUGIN_HOST = "PLUGIN_HOST"
    KNOWLEDGE_HOST = "KNOWLEDGE_HOST"
    API_GATEWAY = "API_GATEWAY"


class _RuntimeNode:
    def __init__(
        self,
        node_id: str,
        cluster_id: str,
        hostname: str,
        status: str = _NodeStatus.INITIALIZING,
        capabilities: Optional[List[str]] = None,
        version: str = "",
        started_at: Optional[datetime] = None,
        last_heartbeat: Optional[datetime] = None,
        health: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
    ):
        self.node_id = node_id
        self.cluster_id = cluster_id
        self.hostname = hostname
        self.status = status
        self.capabilities = capabilities or []
        self.version = version
        self.started_at = started_at or datetime.utcnow()
        self.last_heartbeat = last_heartbeat or datetime.utcnow()
        self.health = health or {}
        self.metadata = metadata or {}
        self.labels = labels or {}

    @property
    def is_online(self) -> bool:
        return self.status == _NodeStatus.ONLINE

    def is_alive(self, timeout_seconds: int = 30) -> bool:
        elapsed = (datetime.utcnow() - self.last_heartbeat).total_seconds()
        return elapsed < timeout_seconds

    def has_capability(self, cap: str) -> bool:
        return cap in self.capabilities


# ── Inline replica of errors ─────────────────────────────────────────


class _NodeNotFoundError(Exception):
    pass


class _NodeAlreadyRegisteredError(Exception):
    pass


# ── Inline replica of NodeRegistry ───────────────────────────────────


class _NodeRegistry:
    _TABLE = "cluster_nodes"

    def __init__(self, db: Any):
        self._db = db

    def _row_to_node(self, row: dict) -> _RuntimeNode:
        return _RuntimeNode(
            node_id=row["node_id"],
            cluster_id=row["cluster_id"],
            hostname=row["hostname"],
            status=row["status"],
            capabilities=json.loads(row["capabilities"]),
            version=row["version"],
            started_at=self._parse_dt(row["started_at"]),
            last_heartbeat=self._parse_dt(row["last_heartbeat"]),
            health=json.loads(row["health"]),
            metadata=json.loads(row["metadata"]),
            labels=json.loads(row["labels"]),
        )

    def _parse_dt(self, val: Any) -> datetime:
        if isinstance(val, datetime):
            return val
        if isinstance(val, str):
            return datetime.fromisoformat(val)
        return datetime.utcnow()

    def _to_json(self, val: Any) -> str:
        return json.dumps(val, default=str)

    async def register(self, node: _RuntimeNode) -> None:
        existing = await self._db.fetch_one(
            f"SELECT node_id FROM {self._TABLE} WHERE node_id=?",
            [node.node_id],
        )
        if existing:
            raise _NodeAlreadyRegisteredError(f"Node already registered: {node.node_id}")

        await self._db.execute(
            f"""INSERT INTO {self._TABLE}
                (node_id, cluster_id, hostname, status, capabilities,
                 version, started_at, last_heartbeat, health, metadata, labels)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                node.node_id,
                node.cluster_id,
                node.hostname,
                node.status,
                self._to_json(node.capabilities),
                node.version,
                node.started_at.isoformat() if isinstance(node.started_at, datetime) else node.started_at,
                node.last_heartbeat.isoformat() if isinstance(node.last_heartbeat, datetime) else node.last_heartbeat,
                self._to_json(node.health),
                self._to_json(node.metadata),
                self._to_json(node.labels),
            ],
        )

    async def get(self, node_id: str) -> Optional[_RuntimeNode]:
        row = await self._db.fetch_one(
            f"SELECT * FROM {self._TABLE} WHERE node_id=?",
            [node_id],
        )
        if not row:
            return None
        return self._row_to_node(dict(row))

    async def list(self, status: Optional[str] = None) -> List[_RuntimeNode]:
        if status:
            rows = await self._db.fetch_all(
                f"SELECT * FROM {self._TABLE} WHERE status=? ORDER BY hostname",
                [status],
            )
        else:
            rows = await self._db.fetch_all(
                f"SELECT * FROM {self._TABLE} ORDER BY hostname",
            )
        return [self._row_to_node(dict(r)) for r in rows]

    async def update_status(self, node_id: str, status: str) -> None:
        existing = await self._db.fetch_one(
            f"SELECT node_id FROM {self._TABLE} WHERE node_id=?",
            [node_id],
        )
        if not existing:
            raise _NodeNotFoundError(f"Node not found: {node_id}")

        await self._db.execute(
            f"UPDATE {self._TABLE} SET status=? WHERE node_id=?",
            [status, node_id],
        )

    async def heartbeat(self, node_id: str, health: Dict[str, Any]) -> None:
        now = datetime.utcnow().isoformat()
        result = await self._db.execute(
            f"UPDATE {self._TABLE} SET last_heartbeat=?, health=? WHERE node_id=?",
            [now, self._to_json(health), node_id],
        )
        if hasattr(result, "rowcount") and result.rowcount == 0:
            raise _NodeNotFoundError(f"Node not found: {node_id}")

    async def find_orphans(self, timeout_seconds: int = 30) -> List[_RuntimeNode]:
        threshold_iso = (datetime.utcnow() - timedelta(seconds=timeout_seconds)).isoformat()
        rows = await self._db.fetch_all(
            f"""SELECT * FROM {self._TABLE}
                WHERE status IN ('ONLINE', 'DEGRADED', 'INITIALIZING')
                AND last_heartbeat < ?""",
            [threshold_iso],
        )
        return [self._row_to_node(dict(r)) for r in rows]

    async def unregister(self, node_id: str) -> None:
        await self._db.execute(
            f"DELETE FROM {self._TABLE} WHERE node_id=?",
            [node_id],
        )


# ── _TestDB shim ─────────────────────────────────────────────────────


class _TestDB:
    """Synchronous sqlite3 shim with async method signatures."""

    def __init__(self):
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cluster_nodes (
                node_id TEXT PRIMARY KEY,
                cluster_id TEXT NOT NULL,
                hostname TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'INITIALIZING',
                capabilities TEXT NOT NULL DEFAULT '[]',
                version TEXT NOT NULL DEFAULT '',
                started_at DATETIME NOT NULL,
                last_heartbeat DATETIME NOT NULL,
                health TEXT NOT NULL DEFAULT '{}',
                metadata TEXT NOT NULL DEFAULT '{}',
                labels TEXT NOT NULL DEFAULT '{}'
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON cluster_nodes(status)")
        self._conn.commit()

    async def execute(self, sql: str, params: Optional[List[Any]] = None) -> Any:
        cur = self._conn.execute(sql, params or [])
        self._conn.commit()
        return cur

    async def fetch_one(self, sql: str, params: Optional[List[Any]] = None) -> Any:
        cur = self._conn.execute(sql, params or [])
        return cur.fetchone()

    async def fetch_all(self, sql: str, params: Optional[List[Any]] = None) -> List[Any]:
        cur = self._conn.execute(sql, params or [])
        return cur.fetchall()

    def close(self):
        self._conn.close()


# ── Helpers ──────────────────────────────────────────────────────────


def _make_node(overrides: Optional[Dict[str, Any]] = None) -> _RuntimeNode:
    data = {
        "node_id": str(uuid.uuid4()),
        "cluster_id": "test-cluster",
        "hostname": "test-node",
        "status": _NodeStatus.ONLINE,
        "capabilities": [_NodeCapabilities.WORKER],
        "version": "1.0.0",
    }
    if overrides:
        data.update(overrides)
    return _RuntimeNode(**data)


def _old_heartbeat_node(timeout: int = 120) -> _RuntimeNode:
    """Node dengan heartbeat yang sudah expired."""
    old_hb = datetime.utcnow() - timedelta(seconds=timeout)
    return _make_node({
        "status": _NodeStatus.ONLINE,
        "last_heartbeat": old_hb,
        "node_id": str(uuid.uuid4()),
        "hostname": "orphan-node",
    })


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def db():
    _db = _TestDB()
    yield _db
    _db.close()


@pytest.fixture
def registry(db):
    return _NodeRegistry(db)


@pytest.fixture
def sample_node():
    return _make_node()


# ═══════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════


class TestNodeModel:
    def test_defaults(self):
        n = _make_node()
        assert n.node_id
        assert n.cluster_id == "test-cluster"
        assert n.status == _NodeStatus.ONLINE
        assert isinstance(n.started_at, datetime)

    def test_is_online(self):
        n = _make_node()
        assert n.is_online is True
        n.status = _NodeStatus.OFFLINE
        assert n.is_online is False

    def test_is_alive(self):
        n = _make_node()
        assert n.is_alive(30) is True
        n.last_heartbeat = datetime.utcnow() - timedelta(seconds=60)
        assert n.is_alive(30) is False

    def test_has_capability(self):
        n = _make_node({"capabilities": ["WORKER", "PLUGIN_HOST"]})
        assert n.has_capability("WORKER") is True
        assert n.has_capability("SCHEDULER") is False


class TestNodeCRUD:
    @pytest.mark.asyncio
    async def test_register_and_get(self, registry, sample_node):
        await registry.register(sample_node)
        retrieved = await registry.get(sample_node.node_id)
        assert retrieved is not None
        assert retrieved.node_id == sample_node.node_id
        assert retrieved.cluster_id == sample_node.cluster_id
        assert retrieved.hostname == sample_node.hostname

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, registry):
        result = await registry.get("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_register_duplicate_fails(self, registry, sample_node):
        await registry.register(sample_node)
        with pytest.raises(_NodeAlreadyRegisteredError):
            await registry.register(sample_node)

    @pytest.mark.asyncio
    async def test_list_all(self, registry):
        n1 = _make_node({"node_id": str(uuid.uuid4()), "hostname": "alpha"})
        n2 = _make_node({"node_id": str(uuid.uuid4()), "hostname": "beta"})
        await registry.register(n1)
        await registry.register(n2)
        nodes = await registry.list()
        assert len(nodes) == 2

    @pytest.mark.asyncio
    async def test_list_filtered_by_status(self, registry):
        online = _make_node({"node_id": str(uuid.uuid4()), "status": _NodeStatus.ONLINE})
        offline = _make_node({"node_id": str(uuid.uuid4()), "status": _NodeStatus.OFFLINE})
        await registry.register(online)
        await registry.register(offline)
        result = await registry.list(status=_NodeStatus.ONLINE)
        assert len(result) == 1
        assert result[0].node_id == online.node_id

    @pytest.mark.asyncio
    async def test_list_empty(self, registry):
        nodes = await registry.list()
        assert nodes == []


class TestNodeHeartbeat:
    @pytest.mark.asyncio
    async def test_heartbeat_updates_last_heartbeat(self, registry, sample_node):
        await registry.register(sample_node)
        old_hb = sample_node.last_heartbeat
        await registry.heartbeat(sample_node.node_id, {"load": 0.5})
        node = await registry.get(sample_node.node_id)
        assert node is not None
        assert node.last_heartbeat > old_hb or node.last_heartbeat >= old_hb
        assert node.health.get("load") == 0.5

    @pytest.mark.asyncio
    async def test_heartbeat_nonexistent_fails(self, registry):
        with pytest.raises(_NodeNotFoundError):
            await registry.heartbeat("no-such-node", {})


class TestOrphanDetection:
    @pytest.mark.asyncio
    async def test_find_orphans_detects_stale_node(self, registry):
        orphan = _old_heartbeat_node(120)
        await registry.register(orphan)
        orphans = await registry.find_orphans(timeout_seconds=60)
        assert len(orphans) >= 1
        found = [n for n in orphans if n.node_id == orphan.node_id]
        assert len(found) == 1

    @pytest.mark.asyncio
    async def test_find_orphans_ignores_fresh_node(self, registry, sample_node):
        await registry.register(sample_node)
        orphans = await registry.find_orphans(timeout_seconds=60)
        found = [n for n in orphans if n.node_id == sample_node.node_id]
        assert len(found) == 0

    @pytest.mark.asyncio
    async def test_find_orphans_ignores_offline(self, registry):
        offline = _old_heartbeat_node(120)
        offline.status = _NodeStatus.OFFLINE
        await registry.register(offline)
        orphans = await registry.find_orphans(timeout_seconds=60)
        found = [n for n in orphans if n.node_id == offline.node_id]
        assert len(found) == 0


class TestNodeUnregister:
    @pytest.mark.asyncio
    async def test_unregister_removes_node(self, registry, sample_node):
        await registry.register(sample_node)
        await registry.unregister(sample_node.node_id)
        result = await registry.get(sample_node.node_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_does_not_error(self, registry):
        # should not raise
        await registry.unregister("no-such-node")


class TestNodeStatusTransition:
    @pytest.mark.asyncio
    async def test_update_status(self, registry, sample_node):
        await registry.register(sample_node)
        await registry.update_status(sample_node.node_id, _NodeStatus.DEGRADED)
        node = await registry.get(sample_node.node_id)
        assert node is not None
        assert node.status == _NodeStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_update_status_nonexistent_fails(self, registry):
        with pytest.raises(_NodeNotFoundError):
            await registry.update_status("no-such", _NodeStatus.ONLINE)
