"""Tests for Working Memory — Sprint 29 Fase 1.

Coverage:
  - WorkingMemoryEntry TTL and expiry
  - WorkingMemory: get/set/delete/clear/snapshot
  - WorkingMemoryManager: session isolation, cross-session operations
  - TTL edge cases (zero, negative, expiry timing)
"""

import time
from datetime import datetime, timezone

import pytest

from sam.cognition.memory import (
    WorkingMemory,
    WorkingMemoryManager,
    WorkingMemoryEntry,
    DEFAULT_TTL,
)


# ── WorkingMemoryEntry Tests ──────────────────────────────────────


class TestWorkingMemoryEntry:
    def test_create_default_ttl(self):
        e = WorkingMemoryEntry(key="k", value=42)
        assert e.key == "k"
        assert e.value == 42
        assert e.ttl == DEFAULT_TTL
        assert e.created_at is not None

    def test_expired_false_for_zero_ttl(self):
        e = WorkingMemoryEntry(key="k", value=1, ttl=0)
        assert e.expired is False

    def test_expired_false_recent(self):
        e = WorkingMemoryEntry(key="k", value=1, ttl=300)
        assert e.expired is False

    def test_expired_true_after_ttl(self):
        e = WorkingMemoryEntry(key="k", value=1, ttl=0.01)
        time.sleep(0.02)
        assert e.expired is True

    def test_touch_updates_updated_at(self):
        e = WorkingMemoryEntry(key="k", value=1, ttl=300)
        old = e.updated_at
        time.sleep(0.01)
        e.touch()
        assert e.updated_at > old

    def test_to_dict_snapshot(self):
        e = WorkingMemoryEntry(key="k", value={"a": 1}, ttl=60)
        d = e.to_dict()
        assert d["key"] == "k"
        assert d["ttl"] == 60

    def test_create_negative_ttl_no_expiry(self):
        """Negative TTL is treated as no expiry (same as 0)."""
        e = WorkingMemoryEntry(key="k", value=1, ttl=-1)
        assert e.expired is False


# ── WorkingMemory Tests ───────────────────────────────────────────


class TestWorkingMemory:
    @pytest.fixture
    def wm(self):
        return WorkingMemory(session_id="test_session")

    def test_get_nonexistent(self, wm):
        assert wm.get("missing") is None

    def test_set_and_get(self, wm):
        wm.set("key1", "value1")
        assert wm.get("key1") == "value1"

    def test_set_overwrite(self, wm):
        wm.set("key1", "old")
        wm.set("key1", "new")
        assert wm.get("key1") == "new"

    def test_set_with_ttl(self, wm):
        wm.set("temp", "data", ttl=0.01)
        time.sleep(0.02)
        assert wm.get("temp") is None

    def test_delete(self, wm):
        wm.set("k", "v")
        wm.delete("k")
        assert wm.get("k") is None

    def test_delete_nonexistent_no_error(self, wm):
        wm.delete("nothing")  # Should not raise

    def test_clear(self, wm):
        wm.set("a", 1)
        wm.set("b", 2)
        wm.clear()
        assert wm.get("a") is None
        assert wm.get("b") is None
        assert wm.entry_count == 0

    def test_snapshot_empty(self, wm):
        assert wm.snapshot() == {}

    def test_snapshot_all_entries(self, wm):
        wm.set("x", 10)
        wm.set("y", 20)
        snap = wm.snapshot()
        assert snap["x"] == 10
        assert snap["y"] == 20

    def test_snapshot_excludes_expired(self, wm):
        wm.set("keep", "alive")
        wm.set("gone", "dead", ttl=0.01)
        time.sleep(0.02)
        snap = wm.snapshot()
        assert "keep" in snap
        assert "gone" not in snap

    def test_entry_count(self, wm):
        assert wm.entry_count == 0
        wm.set("a", 1)
        assert wm.entry_count == 1
        wm.set("b", 2)
        assert wm.entry_count == 2

    def test_keys(self, wm):
        wm.set("a", 1)
        wm.set("b", 2)
        assert set(wm.keys()) == {"a", "b"}

    def test_set_complex_value(self, wm):
        wm.set("config", {"host": "localhost", "port": 8080})
        val = wm.get("config")
        assert val["host"] == "localhost"
        assert val["port"] == 8080

    def test_set_none_value(self, wm):
        wm.set("null_key", None)
        val = wm.get("null_key")
        assert val is None

    def test_clear_empty(self, wm):
        wm.clear()  # Should not raise
        assert wm.entry_count == 0

    def test_get_expired_returns_none(self, wm):
        wm.set("temp", "data", ttl=0.01)
        time.sleep(0.02)
        assert wm.get("temp") is None


# ── WorkingMemoryManager Tests ────────────────────────────────────


class TestWorkingMemoryManager:
    @pytest.fixture
    def mgr(self):
        return WorkingMemoryManager()

    async def test_set_and_get_default(self, mgr):
        await mgr.set("key1", "value1")
        val = await mgr.get("key1")
        assert val == "value1"

    async def test_get_nonexistent(self, mgr):
        val = await mgr.get("missing")
        assert val is None

    async def test_get_nonexistent_session(self, mgr):
        val = await mgr.get("k", session_id="unknown")
        assert val is None

    async def test_set_with_session_isolation(self, mgr):
        await mgr.set("k", "session_a_val", session_id="a")
        await mgr.set("k", "session_b_val", session_id="b")
        val_a = await mgr.get("k", session_id="a")
        val_b = await mgr.get("k", session_id="b")
        assert val_a == "session_a_val"
        assert val_b == "session_b_val"

    async def test_delete(self, mgr):
        await mgr.set("k", "v")
        await mgr.delete("k")
        assert await mgr.get("k") is None

    async def test_delete_nonexistent(self, mgr):
        await mgr.delete("nothing")  # Should not raise

    async def test_clear(self, mgr):
        await mgr.set("a", 1)
        await mgr.set("b", 2)
        await mgr.clear()
        assert await mgr.get("a") is None

    async def test_clear_nonexistent_session(self, mgr):
        await mgr.clear(session_id="ghost")  # Should not raise

    async def test_clear_all(self, mgr):
        await mgr.set("a", 1, session_id="s1")
        await mgr.set("b", 2, session_id="s2")
        await mgr.clear_all()
        assert await mgr.get("a", session_id="s1") is None
        assert await mgr.get("b", session_id="s2") is None
        assert await mgr.list_sessions() == []

    async def test_snapshot(self, mgr):
        await mgr.set("x", 100)
        snap = await mgr.snapshot()
        assert snap["x"] == 100

    async def test_snapshot_empty_session(self, mgr):
        snap = await mgr.snapshot(session_id="empty")
        assert snap == {}

    async def test_snapshot_all(self, mgr):
        await mgr.set("a", 1, session_id="s1")
        await mgr.set("b", 2, session_id="s2")
        all_snap = await mgr.snapshot_all()
        assert "s1" in all_snap
        assert "s2" in all_snap
        assert all_snap["s1"]["a"] == 1
        assert all_snap["s2"]["b"] == 2

    async def test_list_sessions(self, mgr):
        await mgr.set("k", "v", session_id="s1")
        await mgr.set("k", "v", session_id="s2")
        sessions = await mgr.list_sessions()
        assert set(sessions) == {"s1", "s2"}

    async def test_list_sessions_empty(self, mgr):
        sessions = await mgr.list_sessions()
        assert sessions == []

    async def test_get_session_entry_count(self, mgr):
        await mgr.set("a", 1)
        await mgr.set("b", 2)
        count = await mgr.get_session_entry_count("default")
        assert count == 2

    async def test_get_session_entry_count_unknown(self, mgr):
        count = await mgr.get_session_entry_count("ghost")
        assert count == 0

    async def test_entry_exists_true(self, mgr):
        await mgr.set("k", "v")
        assert await mgr.entry_exists("k") is True

    async def test_entry_exists_false(self, mgr):
        assert await mgr.entry_exists("missing") is False

    async def test_entry_exists_expired(self, mgr):
        await mgr.set("k", "v", ttl=0.01)
        time.sleep(0.02)
        assert await mgr.entry_exists("k") is False

    async def test_ttl_default_applied(self, mgr):
        await mgr.set("k", "v")
        wm = mgr._sessions["default"]
        entry = wm._entries.get("k")
        assert entry is not None
        assert entry.ttl == DEFAULT_TTL

    async def test_ttl_custom(self, mgr):
        await mgr.set("k", "v", ttl=60)
        wm = mgr._sessions["default"]
        entry = wm._entries.get("k")
        assert entry.ttl == 60
