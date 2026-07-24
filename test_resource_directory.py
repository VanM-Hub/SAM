"""
Tests for Cluster Identity & Resource Directory.
Uses inline replica classes + _TestDB shim.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import pytest

# ═══════════════════════════════════════════════════════════════════════
# Inline replicas — Resource Model
# ═══════════════════════════════════════════════════════════════════════

class _ResourceType:
    JOB = "JOB"
    WORKFLOW = "WORKFLOW"
    SERVICE = "SERVICE"
    PLUGIN = "PLUGIN"
    KNOWLEDGE = "KNOWLEDGE"


class _ResourceStatus:
    CREATED = "CREATED"
    LOADED = "LOADED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    RETIRED = "RETIRED"


class _ResourceNotFoundError(Exception):
    pass


class _ResourceOwner:
    def __init__(self, node_id: str, lease_expires_at: datetime, heartbeat_interval: int = 30):
        self.node_id = node_id
        self.lease_expires_at = lease_expires_at
        self.heartbeat_interval = heartbeat_interval

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.lease_expires_at


class _RuntimeResource:
    def __init__(
        self,
        id: str,
        type: str = _ResourceType.JOB,
        name: str = "",
        status: str = _ResourceStatus.CREATED,
        owner: Optional[_ResourceOwner] = None,
        data: Optional[Dict[str, Any]] = None,
        version: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.id = id
        self.type = type
        self.name = name or id
        self.status = status
        self.owner = owner
        self.data = data or {}
        self.version = version
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.metadata = metadata or {}

    @property
    def is_owned(self) -> bool:
        return self.owner is not None

    @property
    def is_orphaned(self) -> bool:
        return self.owner is not None and self.owner.is_expired


# ═══════════════════════════════════════════════════════════════════════
# Inline replica — ResourceManager (minimal)
# ═══════════════════════════════════════════════════════════════════════

class _ResourceManager:
    _TABLE = "runtime_resources"

    def __init__(self, db):
        self._db = db

    async def register(self, resource: _RuntimeResource) -> None:
        params = [
            resource.id, resource.type, resource.name, resource.status,
            resource.owner.node_id if resource.owner else None,
            resource.owner.lease_expires_at.isoformat() if resource.owner else None,
            resource.owner.heartbeat_interval if resource.owner else 30,
            json.dumps(resource.data, default=str),
            resource.version,
            resource.created_at.isoformat(),
            resource.updated_at.isoformat(),
            json.dumps(resource.metadata, default=str),
        ]
        await self._db.execute(
            f"INSERT INTO {self._TABLE} "
            "(id, type, name, status, owner_node_id, lease_expires_at, "
            " heartbeat_interval, data, version, created_at, updated_at, metadata) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", params
        )

    async def get(self, resource_id: str) -> Optional[_RuntimeResource]:
        row = await self._db.fetch_one(
            f"SELECT * FROM {self._TABLE} WHERE id=?", [resource_id]
        )
        if not row:
            return None
        return self._row_to_resource(row) if isinstance(row, dict) else self._row_to_resource(dict(row))

    async def list(self, type: Optional[str] = None) -> List[_RuntimeResource]:
        if type:
            rows = await self._db.fetch_all(
                f"SELECT * FROM {self._TABLE} WHERE type=? ORDER BY name", [type]
            )
        else:
            rows = await self._db.fetch_all(
                f"SELECT * FROM {self._TABLE} ORDER BY type, name"
            )
        return [self._row_to_resource(dict(r)) for r in rows]

    async def _get_row(self, resource_id: str) -> Optional[dict]:
        return await self._db.fetch_one(
            f"SELECT * FROM {self._TABLE} WHERE id=?", [resource_id]
        )

    def _row_to_resource(self, row: dict) -> _RuntimeResource:
        owner = None
        if row["owner_node_id"]:
            try:
                lease_dt = datetime.fromisoformat(row["lease_expires_at"]) if row["lease_expires_at"] else datetime.utcnow()
            except (ValueError, TypeError):
                lease_dt = datetime.utcnow()
            owner = _ResourceOwner(
                node_id=row["owner_node_id"],
                lease_expires_at=lease_dt,
                heartbeat_interval=row["heartbeat_interval"] if row["heartbeat_interval"] is not None else 30,
            )
        return _RuntimeResource(
            id=row["id"],
            type=row["type"],
            name=row["name"],
            status=row["status"],
            owner=owner,
            data=json.loads(row["data"]) if isinstance(row["data"], str) else {},
            version=row["version"],
            metadata=json.loads(row["metadata"]) if isinstance(row["metadata"], str) else {},
        )


# ═══════════════════════════════════════════════════════════════════════
# Inline replica — EventBus (minimal)
# ═══════════════════════════════════════════════════════════════════════

_published_events: List[Dict[str, Any]] = []


class _EventBus:
    def __init__(self):
        self._subscriptions: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable) -> None:
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        self._subscriptions[event_type].append(handler)

    async def publish(self, event: Any) -> None:
        _published_events.append({
            "type": event.type,
            "source": event.source,
            "payload": dict(event.payload),
        })
        handlers = self._subscriptions.get(event.type, [])
        wildcard = self._subscriptions.get("*", [])
        for h in handlers + wildcard:
            try:
                await h(event)
            except Exception:
                pass


def _reset_events():
    _published_events.clear()


# ═══════════════════════════════════════════════════════════════════════
# Inline replica — ResourceDirectory
# ═══════════════════════════════════════════════════════════════════════

RESOURCE_REGISTERED = "resource.registered"
RESOURCE_STATUS_CHANGED = "resource.status_changed"
RESOURCE_DATA_CHANGED = "resource.data_changed"
RESOURCE_OWNER_CHANGED = "resource.owner_changed"
RESOURCE_ORPHAN_RECOVERED = "resource.orphan_recovered"


class _Event:
    def __init__(self, type: str, source: str, payload: dict):
        self.type = type
        self.source = source
        self.payload = payload


class _ResourceDirectory(_ResourceManager):
    def __init__(self, db, event_bus: Optional[_EventBus] = None):
        super().__init__(db)
        self._event_bus = event_bus
        self._watchers: Dict[str, List[Callable]] = {}
        self._subscriptions: Dict[str, List[Callable]] = {}

    async def _publish_event(self, event_type: str, resource: _RuntimeResource) -> None:
        if self._event_bus is None:
            return
        await self._event_bus.publish(_Event(
            type=event_type,
            source="resource_directory",
            payload={
                "resource_id": resource.id,
                "resource_type": resource.type,
                "resource_name": resource.name,
                "status": resource.status,
            },
        ))

    async def _notify_watchers(self, resource: _RuntimeResource, event_type: str) -> None:
        type_key = resource.type
        if type_key in self._watchers:
            for cb in self._watchers[type_key]:
                try:
                    r = cb(resource)
                    if hasattr(r, "__await__"):
                        await r
                except Exception:
                    pass

        for pattern, callbacks in self._subscriptions.items():
            if self._event_type_matches_pattern(event_type, pattern):
                for cb in callbacks:
                    try:
                        r = cb(resource, event_type)
                        if hasattr(r, "__await__"):
                            await r
                    except Exception:
                        pass

    @staticmethod
    def _event_type_matches_pattern(event_type: str, pattern: str) -> bool:
        if pattern == "*":
            return True
        if pattern == event_type:
            return True
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            if event_type.startswith(prefix):
                return True
        return False

    async def register(self, resource: _RuntimeResource) -> None:
        await super().register(resource)
        await self._publish_event(RESOURCE_REGISTERED, resource)
        await self._notify_watchers(resource, RESOURCE_REGISTERED)

    async def watch(
        self, resource_type: str, callback: Callable
    ) -> None:
        type_key = resource_type
        if type_key not in self._watchers:
            self._watchers[type_key] = []
        self._watchers[type_key].append(callback)

    async def subscribe(
        self, pattern: str, callback: Callable
    ) -> None:
        if pattern not in self._subscriptions:
            self._subscriptions[pattern] = []
        self._subscriptions[pattern].append(callback)

    async def query(self, filters: Dict[str, Any]) -> List[_RuntimeResource]:
        all_resources = await self.list()
        results = []
        for res in all_resources:
            if self._match_filters(res, filters):
                results.append(res)
        return results

    async def find_owner(self, resource_id: str) -> Optional[_ResourceOwner]:
        resource = await self.get(resource_id)
        if not resource:
            raise _ResourceNotFoundError(f"Resource not found: {resource_id}")
        return resource.owner

    async def find_orphans(self, timeout_seconds: int = 60) -> List[_RuntimeResource]:
        all_resources = await self.list()
        return [r for r in all_resources if r.is_orphaned]

    def _match_filters(self, resource: _RuntimeResource, filters: Dict[str, Any]) -> bool:
        for key, value in filters.items():
            if key == "type":
                if resource.type != value:
                    return False
            elif key == "status":
                if resource.status != value:
                    return False
            elif key == "name":
                if resource.name != value:
                    return False
            elif key == "owner_node_id":
                if resource.owner is None or resource.owner.node_id != value:
                    return False
            elif key == "owned":
                if value and resource.owner is None:
                    return False
                if not value and resource.owner is not None:
                    return False
            elif key == "orphaned":
                if value and not resource.is_orphaned:
                    return False
                if not value and resource.is_orphaned:
                    return False
            else:
                return False
        return True


# ═══════════════════════════════════════════════════════════════════════
# Inline replica — ClusterIdentity
# ═══════════════════════════════════════════════════════════════════════

def _generate_id() -> str:
    return str(uuid.uuid4())


class _ClusterIdentity:
    def __init__(
        self,
        cluster_id: str = None,
        node_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        evidence_id: Optional[str] = None,
    ):
        self.cluster_id = cluster_id or _generate_id()
        self.node_id = node_id
        self.workflow_id = workflow_id
        self.execution_id = execution_id
        self.evidence_id = evidence_id
        self.created_at = datetime.utcnow()

    @property
    def path(self) -> str:
        parts = [f"cluster:{self.cluster_id}"]
        if self.node_id:
            parts.append(f"node:{self.node_id}")
        if self.workflow_id:
            parts.append(f"workflow:{self.workflow_id}")
        if self.execution_id:
            parts.append(f"execution:{self.execution_id}")
        if self.evidence_id:
            parts.append(f"evidence:{self.evidence_id}")
        return "/".join(parts)

    @property
    def is_root(self) -> bool:
        return all(x is None for x in [self.node_id, self.workflow_id, self.execution_id, self.evidence_id])

    def with_node(self, node_id: str) -> "_ClusterIdentity":
        return _ClusterIdentity(
            cluster_id=self.cluster_id,
            node_id=node_id,
        )

    def with_workflow(self, workflow_id: str) -> "_ClusterIdentity":
        return _ClusterIdentity(
            cluster_id=self.cluster_id,
            node_id=self.node_id,
            workflow_id=workflow_id,
        )

    def with_execution(self, execution_id: str) -> "_ClusterIdentity":
        return _ClusterIdentity(
            cluster_id=self.cluster_id,
            node_id=self.node_id,
            workflow_id=self.workflow_id,
            execution_id=execution_id,
        )

    def with_evidence(self, evidence_id: str) -> "_ClusterIdentity":
        return _ClusterIdentity(
            cluster_id=self.cluster_id,
            node_id=self.node_id,
            workflow_id=self.workflow_id,
            execution_id=self.execution_id,
            evidence_id=evidence_id,
        )


# ═══════════════════════════════════════════════════════════════════════
# _TestDB shim
# ═══════════════════════════════════════════════════════════════════════

class _TestDB:
    def __init__(self):
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS runtime_resources (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'CREATED',
                owner_node_id TEXT,
                lease_expires_at TEXT,
                heartbeat_interval INTEGER DEFAULT 30,
                data TEXT DEFAULT '{}',
                version INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_rm_type ON runtime_resources(type)"
        )
        self._conn.commit()

    async def execute(self, sql: str, params=None):
        if params is not None and not isinstance(params, list):
            params = list(params)
        cur = self._conn.cursor()
        cur.execute(sql, params or [])
        self._conn.commit()
        return cur

    async def fetch_one(self, sql: str, params=None):
        if params is not None and not isinstance(params, list):
            params = list(params)
        cur = self._conn.cursor()
        cur.execute(sql, params or [])
        return cur.fetchone()

    async def fetch_all(self, sql: str, params=None):
        if params is not None and not isinstance(params, list):
            params = list(params)
        cur = self._conn.cursor()
        cur.execute(sql, params or [])
        return cur.fetchall()

    def close(self):
        self._conn.close()


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _make_resource(overrides: Optional[Dict[str, Any]] = None) -> _RuntimeResource:
    data = {
        "id": str(uuid.uuid4()),
        "type": _ResourceType.WORKFLOW,
        "name": "test-resource",
        "status": _ResourceStatus.CREATED,
    }
    if overrides:
        data.update(overrides)
    return _RuntimeResource(**data)


def _make_owner(node_id: str = "node-1", lease_seconds: int = 60) -> _ResourceOwner:
    return _ResourceOwner(
        node_id=node_id,
        lease_expires_at=datetime.utcnow() + timedelta(seconds=lease_seconds),
    )


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def db():
    _db = _TestDB()
    yield _db
    _db.close()


@pytest.fixture
def directory(db):
    return _ResourceDirectory(db)


@pytest.fixture
def directory_with_bus(db):
    bus = _EventBus()
    return _ResourceDirectory(db, event_bus=bus)


# ═══════════════════════════════════════════════════════════════════════
# ClusterIdentity Tests
# ═══════════════════════════════════════════════════════════════════════

class TestClusterIdentity:
    def test_generates_cluster_id_by_default(self):
        identity = _ClusterIdentity()
        assert identity.cluster_id is not None
        assert len(identity.cluster_id) > 0

    def test_root_identity(self):
        identity = _ClusterIdentity()
        assert identity.is_root is True
        assert identity.path.startswith("cluster:")

    def test_identity_hierarchy_path(self):
        identity = _ClusterIdentity(
            cluster_id="c1",
            node_id="n1",
            workflow_id="w1",
            execution_id="e1",
            evidence_id="ev1",
        )
        expected = "cluster:c1/node:n1/workflow:w1/execution:e1/evidence:ev1"
        assert identity.path == expected

    def test_partial_hierarchy(self):
        identity = _ClusterIdentity(
            cluster_id="c1",
            node_id="n1",
            workflow_id="w1",
        )
        expected = "cluster:c1/node:n1/workflow:w1"
        assert identity.path == expected

    def test_with_node_creates_new_identity(self):
        root = _ClusterIdentity(cluster_id="c1")
        child = root.with_node("n1")
        assert child.cluster_id == "c1"
        assert child.node_id == "n1"
        assert child.workflow_id is None
        # Root unchanged
        assert root.node_id is None

    def test_identity_chain(self):
        root = _ClusterIdentity(cluster_id="c1")
        n = root.with_node("n1")
        w = n.with_workflow("w1")
        e = w.with_execution("e1")
        ev = e.with_evidence("ev1")
        assert ev.path == "cluster:c1/node:n1/workflow:w1/execution:e1/evidence:ev1"

    def test_identity_not_root_when_child_set(self):
        identity = _ClusterIdentity(cluster_id="c1", node_id="n1")
        assert identity.is_root is False


# ═══════════════════════════════════════════════════════════════════════
# ResourceDirectory — Query Tests
# ═══════════════════════════════════════════════════════════════════════

class TestDirectoryQuery:
    @pytest.mark.asyncio
    async def test_query_by_type(self, directory):
        wf = _make_resource({"type": _ResourceType.WORKFLOW})
        job = _make_resource({"type": _ResourceType.JOB})
        await directory.register(wf)
        await directory.register(job)

        results = await directory.query({"type": _ResourceType.WORKFLOW})
        assert len(results) == 1
        assert results[0].id == wf.id

    @pytest.mark.asyncio
    async def test_query_by_status(self, directory):
        active = _make_resource({"status": _ResourceStatus.ACTIVE})
        created = _make_resource({"status": _ResourceStatus.CREATED})
        await directory.register(active)
        await directory.register(created)

        results = await directory.query({"status": _ResourceStatus.ACTIVE})
        assert len(results) == 1
        assert results[0].id == active.id

    @pytest.mark.asyncio
    async def test_query_by_name(self, directory):
        r1 = _make_resource({"name": "alpha"})
        r2 = _make_resource({"name": "beta"})
        await directory.register(r1)
        await directory.register(r2)

        results = await directory.query({"name": "alpha"})
        assert len(results) == 1
        assert results[0].id == r1.id

    @pytest.mark.asyncio
    async def test_query_multiple_filters(self, directory):
        owner = _make_owner("node-a", 60)
        r1 = _RuntimeResource(
            id=str(uuid.uuid4()),
            type=_ResourceType.WORKFLOW,
            name="wf-a",
            status=_ResourceStatus.ACTIVE,
            owner=owner,
        )
        r2 = _RuntimeResource(
            id=str(uuid.uuid4()),
            type=_ResourceType.WORKFLOW,
            name="wf-b",
            status=_ResourceStatus.CREATED,
        )
        await directory.register(r1)
        await directory.register(r2)

        results = await directory.query({
            "type": _ResourceType.WORKFLOW,
            "status": _ResourceStatus.ACTIVE,
        })
        assert len(results) == 1
        assert results[0].id == r1.id

    @pytest.mark.asyncio
    async def test_query_owned_true(self, directory):
        owned = _make_resource(overrides={"owner": _make_owner("n1", 60)})
        unowned = _make_resource()
        await directory.register(owned)
        await directory.register(unowned)

        results = await directory.query({"owned": True})
        assert len(results) == 1
        assert results[0].id == owned.id

    @pytest.mark.asyncio
    async def test_query_owned_false(self, directory):
        owned = _make_resource(overrides={"owner": _make_owner("n1", 60)})
        unowned = _make_resource()
        await directory.register(owned)
        await directory.register(unowned)

        results = await directory.query({"owned": False})
        assert len(results) == 1
        assert results[0].id == unowned.id

    @pytest.mark.asyncio
    async def test_query_orphaned_false(self, directory):
        fresh_owner = _make_owner("n1", 60)
        fresh = _make_resource(overrides={"owner": fresh_owner})
        orphaned_res = _make_resource(
            overrides={"owner": _make_owner("n2", -1)}  # expired
        )
        await directory.register(fresh)
        await directory.register(orphaned_res)

        results = await directory.query({"orphaned": False})
        assert len(results) == 1
        assert results[0].id == fresh.id

    @pytest.mark.asyncio
    async def test_query_unknown_key_returns_empty(self, directory):
        r = _make_resource()
        await directory.register(r)
        results = await directory.query({"nonexistent": "value"})
        assert results == []

    @pytest.mark.asyncio
    async def test_query_empty_filters_returns_all(self, directory):
        r1 = _make_resource()
        r2 = _make_resource()
        await directory.register(r1)
        await directory.register(r2)
        results = await directory.query({})
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_query_no_match(self, directory):
        r = _make_resource()
        await directory.register(r)
        results = await directory.query({"type": _ResourceType.KNOWLEDGE})
        assert results == []


# ═══════════════════════════════════════════════════════════════════════
# ResourceDirectory — Watch Tests
# ═══════════════════════════════════════════════════════════════════════

class TestDirectoryWatch:
    @pytest.mark.asyncio
    async def test_watch_called_on_register(self, directory):
        called = []
        async def watcher(resource):
            called.append(resource.id)

        await directory.watch(_ResourceType.WORKFLOW, watcher)
        r = _make_resource()
        await directory.register(r)
        assert len(called) == 1
        assert called[0] == r.id

    @pytest.mark.asyncio
    async def test_watch_not_called_for_different_type(self, directory):
        called = []
        async def watcher(resource):
            called.append(resource.id)

        await directory.watch(_ResourceType.JOB, watcher)
        r = _make_resource(overrides={"type": _ResourceType.WORKFLOW})
        await directory.register(r)
        assert len(called) == 0

    @pytest.mark.asyncio
    async def test_multiple_watchers_same_type(self, directory):
        calls1 = []
        calls2 = []

        async def w1(r):
            calls1.append(r.id)

        async def w2(r):
            calls2.append(r.id)

        await directory.watch(_ResourceType.WORKFLOW, w1)
        await directory.watch(_ResourceType.WORKFLOW, w2)

        r = _make_resource()
        await directory.register(r)

        assert len(calls1) == 1
        assert len(calls2) == 1

    @pytest.mark.asyncio
    async def test_sync_watcher(self, directory):
        called = []

        def watcher(resource):
            called.append(resource.id)

        await directory.watch(_ResourceType.WORKFLOW, watcher)
        r = _make_resource()
        await directory.register(r)
        assert len(called) == 1


# ═══════════════════════════════════════════════════════════════════════
# ResourceDirectory — Subscribe Tests
# ═══════════════════════════════════════════════════════════════════════

class TestDirectorySubscribe:
    @pytest.mark.asyncio
    async def test_subscribe_wildcard(self, directory):
        events = []
        async def handler(resource, event_type):
            events.append((resource.id, event_type))

        await directory.subscribe("*", handler)
        r = _make_resource()
        await directory.register(r)

        assert len(events) == 1
        assert events[0][0] == r.id
        assert events[0][1] == RESOURCE_REGISTERED

    @pytest.mark.asyncio
    async def test_subscribe_specific_pattern(self, directory):
        events = []
        async def handler(resource, event_type):
            events.append((resource.id, event_type))

        await directory.subscribe(RESOURCE_REGISTERED, handler)
        r = _make_resource()
        await directory.register(r)

        assert len(events) == 1
        assert events[0][1] == RESOURCE_REGISTERED

    @pytest.mark.asyncio
    async def test_subscribe_pattern_not_matching(self, directory):
        events = []
        async def handler(resource, event_type):
            events.append((resource.id, event_type))

        # Only watch status_changed
        await directory.subscribe(RESOURCE_STATUS_CHANGED, handler)
        r = _make_resource()
        await directory.register(r)

        # register does not trigger status_changed
        assert len(events) == 0


# ═══════════════════════════════════════════════════════════════════════
# ResourceDirectory — find_owner & find_orphans Tests
# ═══════════════════════════════════════════════════════════════════════

class TestDirectoryFindOwner:
    @pytest.mark.asyncio
    async def test_find_owner_returns_owner(self, directory):
        owner = _make_owner("node-x", 60)
        r = _make_resource(overrides={"owner": owner})
        await directory.register(r)

        found = await directory.find_owner(r.id)
        assert found is not None
        assert found.node_id == "node-x"

    @pytest.mark.asyncio
    async def test_find_owner_no_owner(self, directory):
        r = _make_resource()  # no owner
        await directory.register(r)

        found = await directory.find_owner(r.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_find_owner_nonexistent(self, directory):
        with pytest.raises(_ResourceNotFoundError):
            await directory.find_owner("nonexistent")


class TestDirectoryFindOrphans:
    @pytest.mark.asyncio
    async def test_find_orphans_detects_expired(self, directory):
        expired_owner = _make_owner("node-x", -10)  # expired 10 seconds ago
        fresh_owner = _make_owner("node-y", 60)

        orphan = _make_resource(overrides={"owner": expired_owner})
        healthy = _make_resource(overrides={"owner": fresh_owner})
        no_owner = _make_resource()

        await directory.register(orphan)
        await directory.register(healthy)
        await directory.register(no_owner)

        orphans = await directory.find_orphans()
        assert len(orphans) == 1
        assert orphans[0].id == orphan.id

    @pytest.mark.asyncio
    async def test_find_orphans_no_orphans(self, directory):
        owner = _make_owner("node-x", 60)
        r = _make_resource(overrides={"owner": owner})
        await directory.register(r)

        orphans = await directory.find_orphans()
        assert orphans == []


# ═══════════════════════════════════════════════════════════════════════
# ResourceDirectory — EventBus Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestDirectoryEventBus:
    @pytest.mark.asyncio
    async def test_register_publishes_event(self, directory_with_bus):
        _reset_events()
        r = _make_resource()
        await directory_with_bus.register(r)

        assert len(_published_events) >= 1
        matching = [e for e in _published_events if e["type"] == RESOURCE_REGISTERED]
        assert len(matching) == 1
        assert matching[0]["payload"]["resource_id"] == r.id

    @pytest.mark.asyncio
    async def test_event_bus_subscriber_receives_event(self, directory_with_bus, db):
        _reset_events()
        eb = _EventBus()
        dir2 = _ResourceDirectory(db, event_bus=eb)

        received = []
        async def handler(event):
            received.append(event.type)

        eb.subscribe(RESOURCE_REGISTERED, handler)
        r = _make_resource()
        await dir2.register(r)

        assert RESOURCE_REGISTERED in received

    @pytest.mark.asyncio
    async def test_directory_without_bus_does_not_publish(self, directory):
        _reset_events()
        r = _make_resource()
        await directory.register(r)

        matching = [e for e in _published_events if e["type"] == RESOURCE_REGISTERED]
        # No events because directory was created without event_bus
        assert len(matching) == 0
