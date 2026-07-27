"""Tests for Context Window — Sprint 29 Fase 4.

Coverage:
  - ContextItem creation, TTL, expiry, serialization
  - ContextWindow: set/get/delete/list/prune/snapshot/count/clear
  - Importance filtering
  - Max items eviction
  - Edge cases
"""

import time
from datetime import datetime, timezone, timedelta

import pytest

from sam.cognition.context import ContextItem, ContextWindow, DEFAULT_CONTEXT_TTL


# ── ContextItem Tests ─────────────────────────────────────────────


class TestContextItem:
    def test_create_default(self):
        item = ContextItem(key="test", value="data")
        assert item.key == "test"
        assert item.value == "data"
        assert item.importance == 0.5
        assert item.ttl == DEFAULT_CONTEXT_TTL
        assert item.id.startswith("ci_")
        assert item.expires_at is not None

    def test_create_no_expiry(self):
        item = ContextItem(key="perm", value="always", ttl=0)
        assert item.expires_at is None
        assert item.expired is False

    def test_expired_true_after_ttl(self):
        item = ContextItem(key="temp", value="gone", ttl=0.01)
        time.sleep(0.02)
        assert item.expired is True

    def test_expired_false_before_ttl(self):
        item = ContextItem(key="fresh", value="alive", ttl=300)
        assert item.expired is False

    def test_to_dict(self):
        item = ContextItem(key="k", value={"nested": True}, importance=0.8, ttl=120)
        d = item.to_dict()
        assert d["key"] == "k"
        assert d["importance"] == 0.8
        assert d["ttl"] == 120

    def test_from_dict_roundtrip(self):
        item = ContextItem(key="k", value=42, importance=0.9, ttl=60)
        d = item.to_dict()
        item2 = ContextItem.from_dict(d)
        assert item2.key == item.key
        assert item2.value == item.value
        assert item2.importance == item.importance
        assert item2.ttl == item.ttl

    def test_create_custom_id(self):
        item = ContextItem(id="custom_id", key="k", value="v")
        assert item.id == "custom_id"


# ── ContextWindow Tests ───────────────────────────────────────────


class TestContextWindow:
    @pytest.fixture
    def cw(self):
        return ContextWindow(max_items=10, default_ttl=300)

    async def test_set_and_get(self, cw):
        await cw.set("key1", "value1")
        val = await cw.get("key1")
        assert val == "value1"

    async def test_get_missing(self, cw):
        val = await cw.get("nothing")
        assert val is None

    async def test_update_existing(self, cw):
        await cw.set("k", "old")
        await cw.set("k", "new")
        val = await cw.get("k")
        assert val == "new"

    async def test_update_importance(self, cw):
        await cw.set("k", "v", importance=0.3)
        await cw.set("k", "v2", importance=0.9)
        item = await cw.get_item("k")
        assert item.importance == 0.9

    async def test_delete(self, cw):
        await cw.set("k", "v")
        await cw.delete("k")
        assert await cw.get("k") is None

    async def test_delete_missing(self, cw):
        await cw.delete("ghost")  # Should not raise

    async def test_list_empty(self, cw):
        items = await cw.list()
        assert items == []

    async def test_list_all(self, cw):
        await cw.set("a", 1)
        await cw.set("b", 2)
        items = await cw.list()
        assert len(items) == 2

    async def test_list_filter_importance(self, cw):
        await cw.set("high", "important", importance=0.9)
        await cw.set("low", "trivial", importance=0.05)
        items = await cw.list(min_importance=0.5)
        assert len(items) == 1
        assert items[0].key == "high"

    async def test_snapshot(self, cw):
        await cw.set("x", 100)
        await cw.set("y", 200)
        snap = await cw.snapshot()
        assert snap["x"] == 100
        assert snap["y"] == 200

    async def test_snapshot_excludes_expired(self, cw):
        await cw.set("alive", "yes")
        await cw.set("dead", "no", ttl=0.01)
        time.sleep(0.02)
        snap = await cw.snapshot()
        assert "alive" in snap
        assert "dead" not in snap

    async def test_count(self, cw):
        assert await cw.count() == 0
        await cw.set("a", 1)
        assert await cw.count() == 1

    async def test_clear(self, cw):
        await cw.set("a", 1)
        await cw.set("b", 2)
        await cw.clear()
        assert await cw.count() == 0

    async def test_get_expired_returns_none(self, cw):
        await cw.set("temp", "data", ttl=0.01)
        time.sleep(0.02)
        val = await cw.get("temp")
        assert val is None

    async def test_get_item_full(self, cw):
        await cw.set("k", "v", importance=0.7, ttl=60)
        item = await cw.get_item("k")
        assert item is not None
        assert item.importance == 0.7
        assert item.ttl == 60

    async def test_get_item_missing(self, cw):
        assert await cw.get_item("nothing") is None

    async def test_get_item_expired(self, cw):
        await cw.set("gone", "x", ttl=0.01)
        time.sleep(0.02)
        assert await cw.get_item("gone") is None

    # ── Pruning ──────────────────────────────────────────────────

    async def test_prune_removes_expired(self, cw):
        await cw.set("live", "ok")
        await cw.set("dead", "no", ttl=0.01)
        time.sleep(0.02)
        removed = await cw.prune()
        assert removed == 1
        assert await cw.count() == 1

    async def test_prune_removes_low_importance(self, cw):
        await cw.set("important", "high", importance=0.9)
        await cw.set("trivial", "low", importance=0.01)
        removed = await cw.prune()
        assert removed == 1
        assert await cw.count() == 1
        assert await cw.get("important") == "high"

    async def test_prune_noop_if_all_valid(self, cw):
        await cw.set("a", 1, importance=0.5)
        await cw.set("b", 2, importance=0.5)
        removed = await cw.prune()
        assert removed == 0
        assert await cw.count() == 2

    async def test_prune_clean_state(self, cw):
        """After prune, listing should return only valid items."""
        await cw.set("perm", "keep", ttl=0)
        await cw.set("temp", "remove", ttl=0.01)
        time.sleep(0.02)
        await cw.prune()
        items = await cw.list()
        assert len(items) == 1
        assert items[0].key == "perm"

    # ── Max Items Eviction ───────────────────────────────────────

    async def test_evict_lowest_importance_at_capacity(self, cw):
        cw._max_items = 3
        await cw.set("high", "a", importance=0.9)
        await cw.set("mid", "b", importance=0.5)
        await cw.set("low", "c", importance=0.3)
        # Add a new item — should evict "low" (lowest importance)
        await cw.set("new", "d", importance=0.7)
        assert await cw.get("low") is None
        assert await cw.get("new") == "d"

    async def test_evict_with_all_equal_importance(self, cw):
        cw._max_items = 2
        await cw.set("a", 1, importance=0.5)
        await cw.set("b", 2, importance=0.5)
        # At capacity, one gets evicted
        await cw.set("c", 3, importance=0.5)
        assert await cw.count() == 2  # a evicted, b + c remain

    async def test_evict_empty_window(self, cw):
        cw._max_items = 1
        await cw.set("only", "item")
        assert await cw.count() == 1

    async def test_set_string_value(self, cw):
        await cw.set("msg", "hello world")
        assert await cw.get("msg") == "hello world"

    async def test_set_none_value(self, cw):
        await cw.set("null", None)
        assert await cw.get("null") is None

    async def test_set_list_value(self, cw):
        await cw.set("list", [1, 2, 3])
        assert await cw.get("list") == [1, 2, 3]

    async def test_set_dict_value(self, cw):
        await cw.set("config", {"host": "localhost"})
        assert await cw.get("config") == {"host": "localhost"}

    async def test_importance_clamped(self, cw):
        await cw.set("k", "v", importance=2.0)
        item = await cw.get_item("k")
        assert item.importance == 1.0
        await cw.set("k2", "v2", importance=-1.0)
        item2 = await cw.get_item("k2")
        assert item2.importance == 0.0
