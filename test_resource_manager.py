"""
Tests for ResourceManager and ownership model.

Covers:
- register/get/list/update_status
- claim, renew_lease, release
- recover_orphaned
- transfer ownership
"""

import os
import sqlite3
import sys
import tempfile
import uuid
from datetime import datetime, timedelta

import pytest

# ensure src/ on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from sam.core.resource import (
    RuntimeResource,
    ResourceType,
    ResourceStatus,
    ResourceOwner,
    ResourceNotFoundError,
    ResourceOwnershipConflictError,
    ResourceNotOwnedError,
)
from sam.core.resource_manager import ResourceManager


class _TestDB:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def _init_schema(self):
        sql = """
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
        """
        self._conn.execute(sql)
        self._conn.commit()

    async def execute(self, sql: str, params=None):
        if params is not None and not isinstance(params, list):
            params = list(params)
        cur = self._conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        self._conn.commit()

    async def fetch_one(self, sql: str, params=None):
        if params is not None and not isinstance(params, list):
            params = list(params)
        cur = self._conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur.fetchone()

    async def fetch_all(self, sql: str, params=None):
        if params is not None and not isinstance(params, list):
            params = list(params)
        cur = self._conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur.fetchall()

    def close(self):
        self._conn.close()


@pytest.fixture
def db(tmp_path):
    db_path = os.path.join(str(tmp_path), "rm_test.db")
    db = _TestDB(db_path)
    db._init_schema()
    yield db
    db.close()


@pytest.fixture
def rm(db):
    return ResourceManager(db=db)


def _make_resource(rid=None, rtype=ResourceType.SERVICE, name=None, status=ResourceStatus.CREATED):
    rid = rid or str(uuid.uuid4())
    name = name or f"res-{rid[:8]}"
    now = datetime.utcnow().isoformat()
    return RuntimeResource(
        id=rid,
        type=rtype,
        name=name,
        status=status,
        owner=None,
        data={"foo": "bar"},
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata={}
    )


class TestResourceCRUD:
    @pytest.mark.asyncio
    async def test_register_get_list(self, rm):
        r = _make_resource(rtype=ResourceType.WORKFLOW, name="wf-1")
        await rm.register(r)
        got = await rm.get(r.id)
        assert got is not None
        assert got.id == r.id
        assert got.type == ResourceType.WORKFLOW

        listed = await rm.list()
        assert any(x.id == r.id for x in listed)

    @pytest.mark.asyncio
    async def test_update_status(self, rm):
        r = _make_resource(name="svc-1", rtype=ResourceType.SERVICE)
        await rm.register(r)
        updated = await rm.update_status(r.id, ResourceStatus.ACTIVE)
        assert updated.status == ResourceStatus.ACTIVE
        # confirm persisted
        got = await rm.get(r.id)
        assert got.status == ResourceStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, rm):
        assert await rm.get("nope") is None


class TestOwnership:
    @pytest.mark.asyncio
    async def test_claim_and_release(self, rm):
        r = _make_resource()
        await rm.register(r)
        node = "node-a"
        claimed = await rm.claim(r.id, node, lease_seconds=2)
        assert claimed is True
        got = await rm.get(r.id)
        assert got.owner is not None
        assert got.owner.node_id == node

        # renew
        renewed = await rm.renew_lease(r.id, node, lease_seconds=5)
        assert renewed is True
        got2 = await rm.get(r.id)
        assert got2.owner.remaining_seconds > 0

        # release
        await rm.release(r.id, node)
        released = await rm.get(r.id)
        assert released.owner is None

    @pytest.mark.asyncio
    async def test_claim_conflict(self, rm):
        r = _make_resource()
        await rm.register(r)
        await rm.claim(r.id, "node-a", lease_seconds=60)
        with pytest.raises(ResourceOwnershipConflictError):
            await rm.claim(r.id, "node-b", lease_seconds=60)

    @pytest.mark.asyncio
    async def test_renew_by_other_fails(self, rm):
        r = _make_resource()
        await rm.register(r)
        await rm.claim(r.id, "node-a", lease_seconds=60)
        ok = await rm.renew_lease(r.id, "node-b", lease_seconds=30)
        assert ok is False
        # still owned by node-a
        got = await rm.get(r.id)
        assert got.owner.node_id == "node-a"

    @pytest.mark.asyncio
    async def test_release_by_other_fails(self, rm):
        r = _make_resource()
        await rm.register(r)
        await rm.claim(r.id, "owner-1", lease_seconds=60)
        with pytest.raises(ResourceOwnershipConflictError):
            await rm.release(r.id, "other-node")


class TestRecoverAndTransfer:
    @pytest.mark.asyncio
    async def test_recover_orphaned(self, rm):
        r1 = _make_resource()
        r2 = _make_resource()
        await rm.register(r1)
        await rm.register(r2)
        # claim both with short lease
        await rm.claim(r1.id, "node-x", lease_seconds=1)
        await rm.claim(r2.id, "node-y", lease_seconds=1)

        # wait until expired
        import time

        time.sleep(2)

        orphans = await rm.recover_orphaned(timeout_seconds=1)
        # Both should be returned and ownership cleared
        ids = {o.id for o in orphans}
        assert r1.id in ids and r2.id in ids
        # confirm DB cleared
        got1 = await rm.get(r1.id)
        assert got1.owner is None

    @pytest.mark.asyncio
    async def test_transfer(self, rm):
        r = _make_resource()
        await rm.register(r)
        await rm.claim(r.id, "node-from", lease_seconds=60)
        transferred = await rm.transfer(r.id, "node-from", "node-to", lease_seconds=30)
        assert transferred is True
        got = await rm.get(r.id)
        assert got.owner.node_id == "node-to"

    @pytest.mark.asyncio
    async def test_transfer_by_non_owner_fails(self, rm):
        r = _make_resource()
        await rm.register(r)
        # not claimed
        with pytest.raises(ResourceNotOwnedError):
            await rm.transfer(r.id, "node-from", "node-to")

