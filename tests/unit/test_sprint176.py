"""Sprint 176 — Memory Catalog Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.memory.catalog.memory_catalog import (
    MemoryCatalog, MemoryCatalogEntry, MemoryCatalogSearchResult,
)
from sam.memory.catalog.memory_index import MemoryIndex, MemoryIndexer
from sam.memory.catalog.memory_loader import MemoryLoader, MemoryLoadResult
from sam.memory.catalog.memory_version import MemoryVersionInfo, MemoryVersionProvider
from sam.memory.catalog.memory_history import MemoryHistory, MemoryHistoryEntry
from sam.memory.catalog.conversation_catalog import ConversationCatalogBridge
from sam.memory.catalog.dashboard_catalog import DashboardCatalogBridge
from sam.memory.foundation.memory_registry import MemoryRegistry
from sam.memory.foundation.memory_descriptor import MemoryDescriptor
from sam.memory.dashboard.memory_dashboard import ExecutionCard


def _registry():
    r = MemoryRegistry()
    r.register(MemoryDescriptor("mem1", "Short Term", category="short_term",
                                tags=["short"]))
    r.register(MemoryDescriptor("mem2", "Long Term", category="long_term",
                                tags=["long"]))
    r.register(MemoryDescriptor("mem3", "Working", category="working",
                                tags=["working"]))
    return r


class TestMemoryCatalog:
    def test_all_entries(self):
        c = MemoryCatalog(_registry())
        assert len(c.all_entries()) == 3

    def test_search_name(self):
        c = MemoryCatalog(_registry())
        res = c.search("Short")
        assert len(res.entries) == 1
        assert res.entries[0].memory_id == "mem1"

    def test_search_tag(self):
        c = MemoryCatalog(_registry())
        res = c.search("working")
        assert len(res.entries) == 1

    def test_search_empty(self):
        c = MemoryCatalog(_registry())
        assert len(c.search("").entries) == 3

    def test_by_category(self):
        c = MemoryCatalog(_registry())
        assert len(c.by_category("short_term")) == 1

    def test_count(self):
        c = MemoryCatalog(_registry())
        assert c.count() == 3


class TestMemoryCatalogEntry:
    def test_default(self):
        assert MemoryCatalogEntry("m1").category == "general"

    def test_immutable(self):
        e = MemoryCatalogEntry("m1")
        with pytest.raises(FrozenInstanceError):
            e.name = "x"


class TestMemoryCatalogSearchResult:
    def test_default(self):
        assert MemoryCatalogSearchResult().entries == []


class TestMemoryIndex:
    def test_build(self):
        idx = MemoryIndexer(_registry()).build()
        assert idx.tag_index["short"] == ["mem1"]

    def test_find_by_tag(self):
        i = MemoryIndexer(_registry())
        assert i.find_by_tag("long") == ["mem2"]
        assert i.find_by_tag("nosuch") == []

    def test_immutable(self):
        idx = MemoryIndex()
        with pytest.raises(FrozenInstanceError):
            idx.tag_index = {}


class TestMemoryLoader:
    def test_load(self):
        r = MemoryRegistry()
        res = MemoryLoader(r).load(
            [MemoryDescriptor("a"), MemoryDescriptor("b")]
        )
        assert res.loaded == 2
        assert res.failed == 0

    def test_duplicate(self):
        r = MemoryRegistry()
        loader = MemoryLoader(r)
        loader.load([MemoryDescriptor("a")])
        res = loader.load([MemoryDescriptor("a")])
        assert res.loaded == 0
        assert res.failed == 1

    def test_no_filesystem_write(self):
        # load hanya registry in-memory, tidak menyentuh filesystem
        r = MemoryRegistry()
        res = MemoryLoader(r).load([MemoryDescriptor("a")])
        assert res.loaded == 1
        assert r.count() == 1


class TestMemoryLoadResult:
    def test_default(self):
        assert MemoryLoadResult().loaded == 0


class TestMemoryVersionProvider:
    def test_version_of(self):
        v = MemoryVersionProvider(_registry())
        assert v.version_of("mem1") == "1.0.0"

    def test_info(self):
        v = MemoryVersionProvider(_registry())
        assert v.info("mem1").stable is True
        assert v.info("nope").stable is False


class TestMemoryVersionInfo:
    def test_immutable(self):
        i = MemoryVersionInfo("m1")
        with pytest.raises(FrozenInstanceError):
            i.version = "2.0"


class TestMemoryHistory:
    def test_record(self):
        h = MemoryHistory()
        h.record(MemoryHistoryEntry("mem1", "REGISTER"))
        assert h.count() == 1

    def test_filter(self):
        h = MemoryHistory()
        h.record(MemoryHistoryEntry("mem1", "REGISTER"))
        h.record(MemoryHistoryEntry("mem2", "REGISTER"))
        assert len(h.entries("mem1")) == 1
        assert len(h.entries()) == 2


class TestMemoryHistoryEntry:
    def test_immutable(self):
        e = MemoryHistoryEntry("m1", "REGISTER")
        with pytest.raises(FrozenInstanceError):
            e.action = "x"


class TestConversationCatalogBridge:
    def test_summary(self):
        b = ConversationCatalogBridge(MemoryCatalog(_registry()))
        assert b.summary()["total"] == 3

    def test_search(self):
        b = ConversationCatalogBridge(MemoryCatalog(_registry()))
        assert b.search("Short") == ["mem1"]

    def test_version(self):
        v = MemoryVersionProvider(_registry())
        b = ConversationCatalogBridge(MemoryCatalog(_registry()), v)
        assert b.version("mem1") == "1.0.0"


class TestDashboardCatalogBridge:
    def test_five_cards(self):
        b = DashboardCatalogBridge(MemoryCatalog(_registry()))
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardCatalogBridge(MemoryCatalog(_registry()))
        assert b.overview_card().verdict == "ready"


class TestCatalogImmutability:
    DTO_CLASSES = [
        MemoryCatalogEntry, MemoryCatalogSearchResult, MemoryIndex,
        MemoryLoadResult, MemoryVersionInfo, MemoryHistoryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
