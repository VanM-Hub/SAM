"""
Tests for Runtime State Store (state.py) including:
- CRUD operations
- Optimistic locking (version conflict)
- Recovery (load state after simulated restart)
- Integration with ServiceManager
"""
import json
import os
import sqlite3
import tempfile
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Any

import pytest

from src.sam.core.state import (
    StateStore,
    StateRecord,
    StateType,
    StateSavedEvent,
    StateDeletedEvent,
    OptimisticLockError,
)
from src.sam.core.event_bus import EventBus
from src.sam.core.service_manager import ServiceManager
from src.sam.core.service import RuntimeService
from src.sam.core.health import ServiceHealth


# ── Minimal DB shim (sync sqlite3 for Python 3.8) ─────────────────────

class _TestDB:
    def __init__(self, db_path: str):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def _init_schema(self):
        sql = """
        CREATE TABLE IF NOT EXISTS runtime_state_store (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            data TEXT DEFAULT '{}',
            updated_at TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            UNIQUE(type, name)
        );
        CREATE INDEX IF NOT EXISTS idx_runtime_state_type ON runtime_state_store(type);
        CREATE INDEX IF NOT EXISTS idx_runtime_state_status ON runtime_state_store(status);
        CREATE INDEX IF NOT EXISTS idx_runtime_state_updated ON runtime_state_store(updated_at);
        """
        for statement in sql.split(";"):
            stmt = statement.strip()
            if stmt:
                self._conn.execute(stmt)
        self._conn.commit()

    async def execute(self, sql: str, params=None):
        if params and not isinstance(params, list):
            params = list(params)
        cur = self._conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        self._conn.commit()
        cur.close()

    async def fetch_one(self, sql: str, params=None):
        if params and not isinstance(params, list):
            params = list(params)
        cur = self._conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        row = cur.fetchone()
        cur.close()
        return dict(row) if row else None

    async def fetch_all(self, sql: str, params=None):
        if params and not isinstance(params, list):
            params = list(params)
        cur = self._conn.cursor()
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        rows = [dict(r) for r in cur.fetchall()]
        cur.close()
        return rows

    async def close(self):
        try:
            self._conn.close()
        except Exception:
            pass


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def clk():
    from src.sam.core.clock import FrozenClock
    return FrozenClock(datetime(2026, 7, 24, 0, 0, 0))


@pytest.fixture(scope="function")
def db():
    tmpdir = tempfile.mkdtemp()
    db_path = os.path.join(tmpdir, "test_state.db")
    database = _TestDB(db_path)
    database._init_schema()
    yield database
    database._conn.close()
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture(scope="function")
def store(db):
    return StateStore(db)


@pytest.fixture(scope="function")
def event_bus():
    return EventBus()


@pytest.fixture(scope="function")
def store_with_bus(db, event_bus):
    return StateStore(db=db, event_bus=event_bus)


def _make_record(
    name="test-service",
    type=StateType.SERVICE,
    status="running",
    version=1,
    data=None,
):
    return StateRecord(
        id=str(uuid.uuid4()),
        type=type,
        name=name,
        status=status,
        data=data or {},
        updated_at=datetime(2026, 7, 24, 12, 0, 0),
        version=version,
    )


# ── Test: CRUD ────────────────────────────────────────────────────────

class TestCRUD:
    @pytest.mark.asyncio
    async def test_save_and_get(self, store):
        record = _make_record(name="my-service", status="initialized")
        await store.save(record)

        loaded = await store.get(record.id)
        assert loaded is not None
        assert loaded.id == record.id
        assert loaded.name == "my-service"
        assert loaded.status == "initialized"
        assert loaded.type == StateType.SERVICE
        assert loaded.version == 1

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, store):
        result = await store.get("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_save_all_types(self, store):
        types = list(StateType)
        for t in types:
            rec = _make_record(name=f"{t.value.lower()}-1", type=t)
            await store.save(rec)
            loaded = await store.get(rec.id)
            assert loaded is not None
            assert loaded.type == t

        all_records = await store.list()
        assert len(all_records) == len(types)

    @pytest.mark.asyncio
    async def test_get_by_type(self, store):
        # Save 2 DAEMON + 1 SERVICE
        d1 = _make_record(name="daemon-1", type=StateType.DAEMON)
        d2 = _make_record(name="daemon-2", type=StateType.DAEMON)
        s1 = _make_record(name="service-1", type=StateType.SERVICE)
        await store.save(d1)
        await store.save(d2)
        await store.save(s1)

        daemons = await store.get_by_type(StateType.DAEMON)
        assert len(daemons) == 2

        services = await store.get_by_type("SERVICE")
        assert len(services) == 1

    @pytest.mark.asyncio
    async def test_get_by_name(self, store):
        rec = _make_record(name="unique-service")
        await store.save(rec)

        loaded = await store.get_by_name("unique-service")
        assert loaded is not None
        assert loaded.id == rec.id

        none_result = await store.get_by_name("does-not-exist")
        assert none_result is None

    @pytest.mark.asyncio
    async def test_list_filtered(self, store):
        d1 = _make_record(name="d1", type=StateType.DAEMON)
        s1 = _make_record(name="s1", type=StateType.SERVICE)
        s2 = _make_record(name="s2", type=StateType.SERVICE)
        await store.save(d1)
        await store.save(s1)
        await store.save(s2)

        all_records = await store.list()
        assert len(all_records) == 3

        services = await store.list(type=StateType.SERVICE)
        assert len(services) == 2

        daemons = await store.list(type="DAEMON")
        assert len(daemons) == 1

    @pytest.mark.asyncio
    async def test_delete(self, store):
        rec = _make_record(name="delete-me")
        await store.save(rec)
        assert await store.get(rec.id) is not None

        deleted = await store.delete(rec.id)
        assert deleted is True
        assert await store.get(rec.id) is None

        # Delete nonexistent returns False
        assert await store.delete("ghost") is False

    @pytest.mark.asyncio
    async def test_clear(self, store):
        for i in range(5):
            await store.save(_make_record(name=f"svc-{i}"))
        assert len(await store.list()) == 5

        await store.clear()
        assert len(await store.list()) == 0


# ── Test: Optimistic Locking ──────────────────────────────────────────

class TestOptimisticLocking:
    @pytest.mark.asyncio
    async def test_version_increment_on_update(self, store):
        rec = _make_record(version=1)
        await store.save(rec)
        assert rec.version == 1  # new record

        # Update — version should increment
        rec.status = "stopped"
        await store.save(rec)
        assert rec.version == 2

        loaded = await store.get(rec.id)
        assert loaded.version == 2
        assert loaded.status == "stopped"

    @pytest.mark.asyncio
    async def test_optimistic_lock_conflict(self, store):
        rec = _make_record(version=1)
        await store.save(rec)  # saved with version=1

        # Update once so DB version becomes 2
        rec.status = "updated"
        await store.save(rec)  # now version=2 in DB
        assert rec.version == 2

        # Simulate stale read — still at version 1
        stale = StateRecord(
            id=rec.id,
            type=StateType.SERVICE,
            name=rec.name,
            status="new-status",
            data={},
            updated_at=datetime.now(),
            version=1,  # stale
        )

        with pytest.raises(OptimisticLockError) as exc_info:
            await store.save(stale)
        assert "Version conflict" in str(exc_info.value)
        assert exc_info.value.record_id == rec.id
        assert exc_info.value.expected_version == 1
        assert exc_info.value.actual_version == 2

    @pytest.mark.asyncio
    async def test_double_update_works(self, store):
        """Two sequential updates should each increment version."""
        rec = _make_record(version=1)
        await store.save(rec)
        assert rec.version == 1

        rec.status = "first"
        await store.save(rec)
        assert rec.version == 2

        rec.status = "second"
        await store.save(rec)
        assert rec.version == 3

        loaded = await store.get(rec.id)
        assert loaded.version == 3
        assert loaded.status == "second"


# ── Test: Event Publishing ────────────────────────────────────────────

class TestEventPublishing:
    @pytest.mark.asyncio
    async def test_publishes_saved_event(self, store_with_bus, event_bus):
        events = []
        async def handler(event):
            events.append(event)
        event_bus.subscribe("state.saved", handler)

        rec = _make_record(name="event-test", status="running")
        await store_with_bus.save(rec)

        assert len(events) == 1
        assert events[0].state_id == rec.id
        assert events[0].status == "running"

    @pytest.mark.asyncio
    async def test_publishes_deleted_event(self, store_with_bus, event_bus):
        events = []
        async def handler(event):
            events.append(event)
        # Subscribe to both saved and deleted events
        event_bus.subscribe("state.saved", handler)
        event_bus.subscribe("state.deleted", handler)

        rec = _make_record(name="delete-event")
        await store_with_bus.save(rec)
        await store_with_bus.delete(rec.id)

        assert len(events) == 2  # saved + deleted
        assert events[1].state_id == rec.id

    @pytest.mark.asyncio
    async def test_no_events_without_bus(self, store):
        events = []
        async def handler(event):
            events.append(event)

        rec = _make_record(name="no-bus")
        await store.save(rec)
        await store.delete(rec.id)

        # No errors, no events published
        assert len(events) == 0


# ── Test: Recovery ────────────────────────────────────────────────────

class TestRecovery:
    @pytest.mark.asyncio
    async def test_recover_returns_grouped(self, store):
        d = _make_record(name="d1", type=StateType.DAEMON, status="running")
        s1 = _make_record(name="s1", type=StateType.SERVICE, status="running")
        s2 = _make_record(name="s2", type=StateType.SERVICE, status="stopped")
        w = _make_record(name="w1", type=StateType.WORKFLOW, status="completed")
        await store.save(d)
        await store.save(s1)
        await store.save(s2)
        await store.save(w)

        grouped = await store.recover()
        assert "DAEMON" in grouped
        assert "SERVICE" in grouped
        assert "WORKFLOW" in grouped
        assert len(grouped["SERVICE"]) == 2

    @pytest.mark.asyncio
    async def test_recover_empty(self, store):
        grouped = await store.recover()
        assert grouped == {}

    @pytest.mark.asyncio
    async def test_recover_after_restart(self, db):
        """Simulate a restart: new StateStore instance, same DB."""
        store1 = StateStore(db)
        d = _make_record(name="persistent-daemon", type=StateType.DAEMON)
        s = _make_record(name="persistent-service", type=StateType.SERVICE)
        await store1.save(d)
        await store1.save(s)

        # "Restart" — new StateStore instance
        store2 = StateStore(db)
        grouped = await store2.recover()
        assert "DAEMON" in grouped
        assert "SERVICE" in grouped
        assert len(grouped["SERVICE"]) == 1
        assert grouped["SERVICE"][0].name == "persistent-service"


# ── Test: ServiceManager Integration ──────────────────────────────────

class TestServiceManagerIntegration:
    """Test that ServiceManager saves/restores service states via StateStore."""

    @pytest.mark.asyncio
    async def test_service_state_saved_on_initialize(self, db, event_bus):
        store = StateStore(db=db)
        svc = _make_dummy_service("svc-a")
        mgr = ServiceManager(event_bus=event_bus, state_store=store)
        mgr.register(svc)

        await mgr.initialize_all()

        # Check state was persisted
        records = await store.list(type=StateType.SERVICE)
        names = [r.name for r in records]
        assert "svc-a" in names
        statuses = {r.name: r.status for r in records}
        assert statuses["svc-a"] == "initialized"

    @pytest.mark.asyncio
    async def test_service_state_saved_on_start(self, db, event_bus):
        store = StateStore(db=db)
        svc = _make_dummy_service("svc-b")
        mgr = ServiceManager(event_bus=event_bus, state_store=store)
        mgr.register(svc)
        await mgr.initialize_all()
        await mgr.start_all()

        records = await store.list(type=StateType.SERVICE)
        statuses = {r.name: r.status for r in records}
        assert statuses.get("svc-b") == "running"

    @pytest.mark.asyncio
    async def test_service_state_saved_on_stop(self, db, event_bus):
        store = StateStore(db=db)
        svc = _make_dummy_service("svc-c")
        mgr = ServiceManager(event_bus=event_bus, state_store=store)
        mgr.register(svc)
        await mgr.initialize_all()
        await mgr.start_all()
        await mgr.stop_all()

        records = await store.list(type=StateType.SERVICE)
        statuses = {r.name: r.status for r in records}
        assert statuses.get("svc-c") == "stopped"

    @pytest.mark.asyncio
    async def test_restore_service_states(self, db, event_bus):
        store = StateStore(db=db)
        svc = _make_dummy_service("svc-d")
        mgr = ServiceManager(event_bus=event_bus, state_store=store)
        mgr.register(svc)
        await mgr.initialize_all()
        await mgr.start_all()

        # Simulate restart
        mgr2 = ServiceManager(event_bus=event_bus, state_store=store)
        states = await mgr2.restore_service_states()
        assert "svc-d" in states
        assert states["svc-d"] == "running"

    @pytest.mark.asyncio
    async def test_no_state_store_skips_persistence(self, event_bus):
        """Without StateStore, lifecycle methods should still work."""
        svc = _make_dummy_service("svc-no-store")
        mgr = ServiceManager(event_bus=event_bus)  # no state_store
        mgr.register(svc)
        await mgr.initialize_all()
        await mgr.start_all()

        assert svc.initialized
        assert svc.started

        # restore should return empty
        states = await mgr.restore_service_states()
        assert states == {}


# ── Dummy Service for testing ────────────────────────────────────────

class _DummyService(RuntimeService):
    def __init__(self, name: str):
        super().__init__()
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    async def initialize(self):
        self._initialized = True

    async def start(self):
        self._started = True

    async def stop(self):
        self._stopped = True
        self._started = False

    async def health(self) -> ServiceHealth:
        return ServiceHealth.healthy()


def _make_dummy_service(name: str) -> _DummyService:
    return _DummyService(name)
