"""Sprint 168 — Skill Catalog Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.skills.catalog.skill_catalog import SkillCatalog, CatalogEntry, CatalogSearchResult
from sam.skills.catalog.skill_index import SkillIndex, SkillIndexer
from sam.skills.catalog.skill_loader import SkillLoader, LoadResult
from sam.skills.catalog.skill_version import SkillVersionInfo, SkillVersionProvider
from sam.skills.catalog.skill_history import SkillHistory, SkillHistoryEntry
from sam.skills.catalog.conversation_catalog import ConversationCatalogBridge
from sam.skills.catalog.dashboard_catalog import DashboardCatalogBridge
from sam.skills.foundation.skill_registry import SkillRegistry
from sam.skills.foundation.skill_descriptor import SkillDescriptor
from sam.skills.dashboard.skill_dashboard import ExecutionCard


def _registry():
    r = SkillRegistry()
    r.register(SkillDescriptor("skill1", "Read File", category="io", tags=["read"]))
    r.register(SkillDescriptor("skill2", "Write File", category="io", tags=["write"]))
    r.register(SkillDescriptor("skill3", "Query DB", category="db", tags=["sql"]))
    return r


class TestSkillCatalog:
    def test_all_entries(self):
        c = SkillCatalog(_registry())
        assert len(c.all_entries()) == 3

    def test_search_name(self):
        c = SkillCatalog(_registry())
        res = c.search("Read")
        assert len(res.entries) == 1
        assert res.entries[0].skill_id == "skill1"

    def test_search_category(self):
        c = SkillCatalog(_registry())
        res = c.search("db")
        assert len(res.entries) == 1

    def test_search_empty(self):
        c = SkillCatalog(_registry())
        assert len(c.search("").entries) == 3

    def test_by_category(self):
        c = SkillCatalog(_registry())
        assert len(c.by_category("io")) == 2

    def test_count(self):
        c = SkillCatalog(_registry())
        assert c.count() == 3


class TestCatalogEntry:
    def test_default(self):
        assert CatalogEntry("s1").category == "general"

    def test_immutable(self):
        e = CatalogEntry("s1")
        with pytest.raises(FrozenInstanceError):
            e.name = "x"


class TestCatalogSearchResult:
    def test_default(self):
        assert CatalogSearchResult().entries == []


class TestSkillIndex:
    def test_build(self):
        idx = SkillIndexer(_registry()).build()
        assert "read" in idx.tag_index
        assert idx.tag_index["read"] == ["skill1"]

    def test_find_by_tag(self):
        i = SkillIndexer(_registry())
        assert i.find_by_tag("sql") == ["skill3"]
        assert i.find_by_tag("nosuch") == []

    def test_immutable(self):
        idx = SkillIndex()
        with pytest.raises(FrozenInstanceError):
            idx.tag_index = {}


class TestSkillLoader:
    def test_load(self):
        r = SkillRegistry()
        res = SkillLoader(r).load(
            [SkillDescriptor("a"), SkillDescriptor("b")]
        )
        assert res.loaded == 2
        assert res.failed == 0

    def test_duplicate(self):
        r = SkillRegistry()
        loader = SkillLoader(r)
        loader.load([SkillDescriptor("a")])
        res = loader.load([SkillDescriptor("a")])
        assert res.loaded == 0
        assert res.failed == 1


class TestLoadResult:
    def test_default(self):
        assert LoadResult().loaded == 0


class TestSkillVersionProvider:
    def test_version_of(self):
        v = SkillVersionProvider(_registry())
        assert v.version_of("skill1") == "1.0.0"

    def test_info(self):
        v = SkillVersionProvider(_registry())
        assert v.info("skill1").stable is True


class TestSkillVersionInfo:
    def test_default_stable(self):
        assert SkillVersionInfo("s1").stable is True

    def test_immutable(self):
        i = SkillVersionInfo("s1")
        with pytest.raises(FrozenInstanceError):
            i.version = "2.0"


class TestSkillHistory:
    def test_record(self):
        h = SkillHistory()
        h.record(SkillHistoryEntry("skill1", "REGISTER"))
        assert h.count() == 1

    def test_filter(self):
        h = SkillHistory()
        h.record(SkillHistoryEntry("skill1", "REGISTER"))
        h.record(SkillHistoryEntry("skill2", "REGISTER"))
        assert len(h.entries("skill1")) == 1


class TestSkillHistoryEntry:
    def test_immutable(self):
        e = SkillHistoryEntry("s1", "REGISTER")
        with pytest.raises(FrozenInstanceError):
            e.action = "x"


class TestConversationCatalogBridge:
    def test_summary(self):
        b = ConversationCatalogBridge(SkillCatalog(_registry()))
        assert b.summary()["total"] == 3

    def test_search(self):
        b = ConversationCatalogBridge(SkillCatalog(_registry()))
        assert b.search("Read") == ["skill1"]

    def test_version(self):
        v = SkillVersionProvider(_registry())
        b = ConversationCatalogBridge(SkillCatalog(_registry()), v)
        assert b.version("skill1") == "1.0.0"


class TestDashboardCatalogBridge:
    def test_five_cards(self):
        b = DashboardCatalogBridge(SkillCatalog(_registry()))
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardCatalogBridge(SkillCatalog(_registry()))
        assert b.overview_card().verdict == "ready"


class TestCatalogImmutability:
    DTO_CLASSES = [
        CatalogEntry, CatalogSearchResult, SkillIndex,
        LoadResult, SkillVersionInfo, SkillHistoryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
