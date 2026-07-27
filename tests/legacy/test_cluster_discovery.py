"""
Tests for Cluster Discovery & Heartbeat Service.
Uses inline replica classes + _TestDB shim.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytest

# ── Inline replicas ───────────────────────────────────────────────────

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
    ):
        self.node_id = node_id
        self.cluster_id = cluster_id
        self.hostname = hostname
        self.status = status
        self.capabilities = capabilities or []
        self.version = version
        self.started_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        self.health = {}
        self.metadata = {}
        self.labels = {}

    @property
    def is_online(self) -> bool:
        return self.status == _NodeStatus.ONLINE

    def has_capability(self, cap: str) -> bool:
        return cap in self.capabilities


class _NodeNotFoundError(Exception):
    pass


class _NodeAlreadyRegisteredError(Exception):
    pass


class _NodeRegistry:
    _TABLE = "cluster_nodes"

    def __init__(self, db: Any):
        self._db = db

    def _row_to_node(self, row: dict) -> _RuntimeNode:
        cap = json.loads(row["capabilities"]) if isinstance(row["capabilities"], str) else (row["capabilities"] or [])
        n = _RuntimeNode(
            node_id=row["node_id"],
            cluster_id=row["cluster_id"],
            hostname=row["hostname"],
            status=row["status"],
            capabilities=cap,
            version=row["version"],
        )
        n.started_at = self._parse_dt(row["started_at"])
        n.last_heartbeat = self._parse_dt(row["last_heartbeat"])
        n.health = json.loads(row["health"]) if isinstance(row["health"], str) else (row["health"] or {})
        n.metadata = json.loads(row["metadata"]) if isinstance(row["metadata"], str) else (row["metadata"] or {})
        n.labels = json.loads(row["labels"]) if isinstance(row["labels"], str) else (row["labels"] or {})
        return n

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
                node.node_id, node.cluster_id, node.hostname, node.status,
                self._to_json(node.capabilities), node.version,
                node.started_at.isoformat(), node.last_heartbeat.isoformat(),
                self._to_json(node.health), self._to_json(node.metadata),
                self._to_json(node.labels),
            ],
        )

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

    async def heartbeat(self, node_id: str, health: Dict[str, Any]) -> None:
        now = datetime.utcnow().isoformat()
        result = await self._db.execute(
            f"UPDATE {self._TABLE} SET last_heartbeat=?, health=? WHERE node_id=?",
            [now, self._to_json(health), node_id],
        )
        if hasattr(result, "rowcount") and result.rowcount == 0:
            raise _NodeNotFoundError(f"Node not found: {node_id}")


# ── Inline replica: NodeDiscovery ─────────────────────────────────────


class _NodeDiscovery:
    def __init__(self, registry: _NodeRegistry):
        self._registry = registry

    async def discover_peers(self) -> List[_RuntimeNode]:
        return await self._registry.list()

    async def get_active_nodes(self) -> List[_RuntimeNode]:
        return await self._registry.list(status=_NodeStatus.ONLINE)

    async def get_nodes_with_capability(self, capability: str) -> List[_RuntimeNode]:
        all_nodes = await self._registry.list()
        return [
            n for n in all_nodes
            if n.status == _NodeStatus.ONLINE and n.has_capability(capability)
        ]


# ── Inline Health helpers ─────────────────────────────────────────────


class _HealthStatus:
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class _ServiceHealth:
    def __init__(self, status: str = _HealthStatus.HEALTHY, message: str = ""):
        self.status = status
        self.message = message


class _RuntimeService:
    """Minimal base untuk HeartbeatService test."""
    def __init__(self):
        self._initialized = False
        self._started = False

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def started(self) -> bool:
        return self._started


# ── Inline replica: HeartbeatService ──────────────────────────────────


class _HeartbeatService(_RuntimeService):
    def __init__(
        self,
        node_registry: _NodeRegistry,
        node_id: str,
        interval: float = 0.1,
    ):
        super().__init__()
        self._node_registry = node_registry
        self._node_id = node_id
        self._interval = interval
        self._task: Optional[asyncio.Task] = None
        self._heartbeat_count = 0

    @property
    def heartbeat_count(self) -> int:
        return self._heartbeat_count

    async def initialize(self) -> None:
        self._initialized = True

    async def start(self) -> None:
        if self._started:
            return
        self._started = True
        self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if not self._started:
            return
        self._started = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def health(self) -> _ServiceHealth:
        if not self._started:
            return _ServiceHealth(_HealthStatus.UNHEALTHY, "not started")
        if self._task and self._task.done() and not self._task.cancelled():
            exc = self._task.exception()
            if exc:
                return _ServiceHealth(_HealthStatus.UNHEALTHY, str(exc))
        return _ServiceHealth(_HealthStatus.HEALTHY, f"active, count={self._heartbeat_count}")

    def _collect_health(self) -> Dict[str, Any]:
        return {
            "load": 0.5,
            "queue_count": 3,
            "workflow_count": 1,
            "plugin_count": 2,
            "memory": 128.0,
            "cpu": 25.0,
        }

    async def _run_loop(self) -> None:
        while self._started:
            try:
                health_data = self._collect_health()
                await self._node_registry.heartbeat(self._node_id, health_data)
                self._heartbeat_count += 1
            except asyncio.CancelledError:
                break
            except Exception:
                pass
            await asyncio.sleep(self._interval)


# ── _TestDB shim ──────────────────────────────────────────────────────


class _TestDB:
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


# ── Helpers ───────────────────────────────────────────────────────────


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
def discovery(registry):
    return _NodeDiscovery(registry)


# ═══════════════════════════════════════════════════════════════════════
# Discovery Tests
# ═══════════════════════════════════════════════════════════════════════


class TestNodeDiscovery:
    @pytest.mark.asyncio
    async def test_discover_peers_returns_all(self, discovery, registry):
        n1 = _make_node({"node_id": str(uuid.uuid4()), "hostname": "alpha"})
        n2 = _make_node({"node_id": str(uuid.uuid4()), "hostname": "beta"})
        await registry.register(n1)
        await registry.register(n2)

        peers = await discovery.discover_peers()
        assert len(peers) == 2
        hostnames = {p.hostname for p in peers}
        assert hostnames == {"alpha", "beta"}

    @pytest.mark.asyncio
    async def test_discover_peers_empty(self, discovery):
        peers = await discovery.discover_peers()
        assert peers == []

    @pytest.mark.asyncio
    async def test_get_active_nodes_only_online(self, discovery, registry):
        online = _make_node({"node_id": str(uuid.uuid4()), "status": _NodeStatus.ONLINE})
        offline = _make_node({"node_id": str(uuid.uuid4()), "status": _NodeStatus.OFFLINE})
        degraded = _make_node({"node_id": str(uuid.uuid4()), "status": _NodeStatus.DEGRADED})
        await registry.register(online)
        await registry.register(offline)
        await registry.register(degraded)

        active = await discovery.get_active_nodes()
        assert len(active) == 1
        assert active[0].node_id == online.node_id

    @pytest.mark.asyncio
    async def test_get_nodes_with_capability(self, discovery, registry):
        worker = _make_node({
            "node_id": str(uuid.uuid4()),
            "capabilities": [_NodeCapabilities.WORKER],
        })
        scheduler = _make_node({
            "node_id": str(uuid.uuid4()),
            "capabilities": [_NodeCapabilities.SCHEDULER],
        })
        both = _make_node({
            "node_id": str(uuid.uuid4()),
            "capabilities": [_NodeCapabilities.WORKER, _NodeCapabilities.SCHEDULER],
        })
        offline_worker = _make_node({
            "node_id": str(uuid.uuid4()),
            "status": _NodeStatus.OFFLINE,
            "capabilities": [_NodeCapabilities.WORKER],
        })
        for n in [worker, scheduler, both, offline_worker]:
            await registry.register(n)

        workers = await discovery.get_nodes_with_capability(_NodeCapabilities.WORKER)
        # Only ONLINE nodes with WORKER capability
        assert len(workers) == 2
        worker_ids = {w.node_id for w in workers}
        assert worker.node_id in worker_ids
        assert both.node_id in worker_ids
        assert offline_worker.node_id not in worker_ids

    @pytest.mark.asyncio
    async def test_get_nodes_with_capability_none_found(self, discovery, registry):
        n = _make_node({
            "node_id": str(uuid.uuid4()),
            "capabilities": [_NodeCapabilities.WORKER],
        })
        await registry.register(n)
        result = await discovery.get_nodes_with_capability(_NodeCapabilities.API_GATEWAY)
        assert result == []


# ═══════════════════════════════════════════════════════════════════════
# Heartbeat Tests
# ═══════════════════════════════════════════════════════════════════════


class TestHeartbeatService:
    @pytest.mark.asyncio
    async def test_initialize_sets_initialized(self, registry):
        node = _make_node()
        await registry.register(node)
        hb = _HeartbeatService(registry, node.node_id, interval=0.1)
        assert hb.initialized is False
        await hb.initialize()
        assert hb.initialized is True

    @pytest.mark.asyncio
    async def test_start_sends_heartbeats(self, registry):
        node = _make_node()
        await registry.register(node)
        hb = _HeartbeatService(registry, node.node_id, interval=0.05)

        await hb.initialize()
        await hb.start()
        assert hb.started is True

        # Tunggu beberapa heartbeat
        await asyncio.sleep(0.15)
        assert hb.heartbeat_count >= 1

        # Verifikasi registry menerima update
        retrieved = await registry.list()
        assert len(retrieved) == 1
        assert retrieved[0].health.get("load") == 0.5

        await hb.stop()
        assert hb.started is False

    @pytest.mark.asyncio
    async def test_stop_halts_heartbeats(self, registry):
        node = _make_node()
        await registry.register(node)
        hb = _HeartbeatService(registry, node.node_id, interval=0.01)

        await hb.initialize()
        await hb.start()
        await asyncio.sleep(0.05)
        count_before = hb.heartbeat_count
        await hb.stop()

        # Tunggu — seharusnya tidak ada heartbeat baru
        await asyncio.sleep(0.1)
        assert hb.heartbeat_count == count_before

    @pytest.mark.asyncio
    async def test_health_when_not_started(self, registry):
        node = _make_node()
        await registry.register(node)
        hb = _HeartbeatService(registry, node.node_id, interval=0.1)
        await hb.initialize()
        health = await hb.health()
        assert health.status == _HealthStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_health_when_running(self, registry):
        node = _make_node()
        await registry.register(node)
        hb = _HeartbeatService(registry, node.node_id, interval=0.1)
        await hb.initialize()
        await hb.start()
        health = await hb.health()
        assert health.status == _HealthStatus.HEALTHY
        await hb.stop()

    @pytest.mark.asyncio
    async def test_collect_health_metrics(self, registry):
        node = _make_node()
        await registry.register(node)
        hb = _HeartbeatService(registry, node.node_id, interval=0.1)
        metrics = hb._collect_health()
        assert "load" in metrics
        assert metrics["queue_count"] == 3
        assert metrics["workflow_count"] == 1
        assert metrics["plugin_count"] == 2
        assert metrics["memory"] == 128.0
        assert metrics["cpu"] == 25.0

    @pytest.mark.asyncio
    async def test_double_start_is_idempotent(self, registry):
        node = _make_node()
        await registry.register(node)
        hb = _HeartbeatService(registry, node.node_id, interval=0.1)
        await hb.initialize()
        await hb.start()
        await hb.start()  # kedua kalinya
        assert hb.started is True
        await hb.stop()

    @pytest.mark.asyncio
    async def test_double_stop_is_idempotent(self, registry):
        node = _make_node()
        await registry.register(node)
        hb = _HeartbeatService(registry, node.node_id, interval=0.1)
        await hb.initialize()
        await hb.start()
        await hb.stop()
        await hb.stop()  # kedua kalinya — tidak error
        assert hb.started is False
