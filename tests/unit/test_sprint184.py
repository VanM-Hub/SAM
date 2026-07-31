"""Sprint 184 — Knowledge Catalog Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.knowledge_runtime.catalog.knowledge_catalog import (
    KnowledgeCatalog, KnowledgeCatalogEntry, KnowledgeCatalogSearchResult,
)
from sam.knowledge_runtime.catalog.knowledge_index import (
    KnowledgeIndex, KnowledgeIndexer,
)
from sam.knowledge_runtime.catalog.knowledge_loader import (
    KnowledgeLoader, KnowledgeLoadResult,
)
from sam.knowledge_runtime.catalog.knowledge_version import (
    KnowledgeVersionInfo, KnowledgeVersionProvider,
)
from sam.knowledge_runtime.catalog.knowledge_history import (
    KnowledgeHistory, KnowledgeHistoryEntry,
)
from sam.knowledge_runtime.catalog.conversation_catalog import ConversationCatalogBridge
from sam.knowledge_runtime.catalog.dashboard_catalog import DashboardCatalogBridge
from sam.knowledge_runtime.foundation.knowledge_registry import KnowledgeRegistry
from sam.knowledge_runtime.foundation.knowledge_descriptor import KnowledgeDescriptor
from sam.knowledge_runtime.dashboard.knowledge_dashboard import ExecutionCard


def _registry():
    r = KnowledgeRegistry()
    r.register(KnowledgeDescriptor("kn1", "Domain A", category="domain", tags=["dom"]))
    r.register(KnowledgeDescriptor("kn2", "Domain B", category="domain", tags=["biz"]))
    r.register(KnowledgeDescriptor("kn3", "Tech", category="tech", tags=["tech"]))
    return r


class TestKnowledgeCatalog:
    def test_all_entries(self):
        c = KnowledgeCatalog(_registry())
        assert len(c.all_entries()) == 3

    def test_search_name(self):
        c = KnowledgeCatalog(_registry())
        res = c.search("Domain A")
        assert len(res.entries) == 1
        assert res.entries[0].knowledge_id == "kn1"

    def test_search_tag(self):
        c = KnowledgeCatalog(_registry())
        res = c.search("tech")
        assert len(res.entries) == 1

    def test_search_empty(self):
        c = KnowledgeCatalog(_registry())
        assert len(c.search("").entries) == 3

    def test_by_category(self):
        c = KnowledgeCatalog(_registry())
        assert len(c.by_category("domain")) == 2

    def test_count(self):
        c = KnowledgeCatalog(_registry())
        assert c.count() == 3


class TestKnowledgeCatalogEntry:
    def test_default(self):
        assert KnowledgeCatalogEntry("k1").category == "general"

    def test_immutable(self):
        e = KnowledgeCatalogEntry("k1")
        with pytest.raises(FrozenInstanceError):
            e.name = "x"


class TestKnowledgeCatalogSearchResult:
    def test_default(self):
        assert KnowledgeCatalogSearchResult().entries == []


class TestKnowledgeIndex:
    def test_build(self):
        idx = KnowledgeIndexer(_registry()).build()
        assert idx.tag_index["dom"] == ["kn1"]

    def test_find_by_tag(self):
        i = KnowledgeIndexer(_registry())
        assert i.find_by_tag("biz") == ["kn2"]
        assert i.find_by_tag("nosuch") == []

    def test_immutable(self):
        idx = KnowledgeIndex()
        with pytest.raises(FrozenInstanceError):
            idx.tag_index = {}


class TestKnowledgeLoader:
    def test_load(self):
        r = KnowledgeRegistry()
        res = KnowledgeLoader(r).load(
            [KnowledgeDescriptor("a"), KnowledgeDescriptor("b")]
        )
        assert res.loaded == 2
        assert res.failed == 0

    def test_duplicate(self):
        r = KnowledgeRegistry()
        loader = KnowledgeLoader(r)
        loader.load([KnowledgeDescriptor("a")])
        res = loader.load([KnowledgeDescriptor("a")])
        assert res.loaded == 0
        assert res.failed == 1

    def test_no_store(self):
        r = KnowledgeRegistry()
        res = KnowledgeLoader(r).load([KnowledgeDescriptor("a")])
        assert res.loaded == 1
        assert r.count() == 1


class TestKnowledgeLoadResult:
    def test_default(self):
        assert KnowledgeLoadResult().loaded == 0


class TestKnowledgeVersionProvider:
    def test_version_of(self):
        v = KnowledgeVersionProvider(_registry())
        assert v.version_of("kn1") == "1.0.0"

    def test_info(self):
        v = KnowledgeVersionProvider(_registry())
        assert v.info("kn1").stable is True
        assert v.info("nope").stable is False


class TestKnowledgeVersionInfo:
    def test_immutable(self):
        i = KnowledgeVersionInfo("k1")
        with pytest.raises(FrozenInstanceError):
            i.version = "2.0"


class TestKnowledgeHistory:
    def test_record(self):
        h = KnowledgeHistory()
        h.record(KnowledgeHistoryEntry("kn1", "REGISTER"))
        assert h.count() == 1

    def test_filter(self):
        h = KnowledgeHistory()
        h.record(KnowledgeHistoryEntry("kn1", "REGISTER"))
        h.record(KnowledgeHistoryEntry("kn2", "REGISTER"))
        assert len(h.entries("kn1")) == 1
        assert len(h.entries()) == 2


class TestKnowledgeHistoryEntry:
    def test_immutable(self):
        e = KnowledgeHistoryEntry("kn1", "REGISTER")
        with pytest.raises(FrozenInstanceError):
            e.action = "x"


class TestConversationCatalogBridge:
    def test_summary(self):
        b = ConversationCatalogBridge(KnowledgeCatalog(_registry()))
        assert b.summary()["total"] == 3

    def test_search(self):
        b = ConversationCatalogBridge(KnowledgeCatalog(_registry()))
        assert b.search("Domain A") == ["kn1"]

    def test_version(self):
        v = KnowledgeVersionProvider(_registry())
        b = ConversationCatalogBridge(KnowledgeCatalog(_registry()), v)
        assert b.version("kn1") == "1.0.0"


class TestDashboardCatalogBridge:
    def test_five_cards(self):
        b = DashboardCatalogBridge(KnowledgeCatalog(_registry()))
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardCatalogBridge(KnowledgeCatalog(_registry()))
        assert b.overview_card().verdict == "ready"


class TestCatalogImmutability:
    DTO_CLASSES = [
        KnowledgeCatalogEntry, KnowledgeCatalogSearchResult, KnowledgeIndex,
        KnowledgeLoadResult, KnowledgeVersionInfo, KnowledgeHistoryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
