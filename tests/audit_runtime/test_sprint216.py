"""Sprint 216 — Audit Catalog Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.audit_runtime.catalog.audit_catalog import AuditCatalog
from sam.audit_runtime.catalog.audit_index import AuditIndex, AuditIndexer
from sam.audit_runtime.catalog.audit_loader import AuditLoader, AuditLoadResult
from sam.audit_runtime.catalog.audit_version import (
    AuditVersionInfo, AuditVersionProvider,
)
from sam.audit_runtime.catalog.audit_history import (
    AuditHistory, AuditHistoryEntry, AuditHistoryRecorder,
)
from sam.audit_runtime.catalog.conversation_catalog import (
    ConversationCatalogBridge,
)
from sam.audit_runtime.catalog.dashboard_catalog import DashboardCatalogBridge
from sam.audit_runtime.foundation.audit_descriptor import AuditDescriptor
from sam.audit_runtime.dashboard import PolicyCard


def _catalog():
    return AuditCatalog().add(
        AuditDescriptor("aud1", category="security")).add(
        AuditDescriptor("aud2", category="operations"))


class TestAuditCatalog:
    def test_add(self):
        c = AuditCatalog().add(AuditDescriptor("a"))
        assert c.count() == 1

    def test_get(self):
        c = _catalog()
        assert c.get("aud1").category == "security"

    def test_by_category(self):
        c = _catalog()
        assert len(c.by_category("security")) == 1

    def test_all_entries(self):
        assert len(_catalog().all_entries()) == 2

    def test_immutable(self):
        c = AuditCatalog()
        with pytest.raises(FrozenInstanceError):
            c._entries = {}


class TestAuditIndex:
    def test_contains(self):
        idx = AuditIndex(record_ids=("a", "b"))
        assert idx.contains("a")
        assert idx.size() == 2

    def test_indexer(self):
        idx = AuditIndexer().index([AuditDescriptor("x")])
        assert idx.contains("x")

    def test_immutable(self):
        idx = AuditIndex()
        with pytest.raises(FrozenInstanceError):
            idx.record_ids = ()


class TestAuditLoader:
    def test_load(self):
        res = AuditLoader().load([AuditDescriptor("a"), AuditDescriptor("b")])
        assert res.loaded is True
        assert res.count == 2

    def test_load_empty(self):
        res = AuditLoader().load([])
        assert res.loaded is False
        assert res.count == 0

    def test_no_file(self):
        # loader tidak membaca disk — hanya terima data in-memory
        assert AuditLoader().load([]).loaded is False


class TestAuditLoadResult:
    def test_immutable(self):
        res = AuditLoadResult()
        with pytest.raises(FrozenInstanceError):
            res.loaded = True


class TestAuditVersionProvider:
    def test_get(self):
        v = AuditVersionProvider().get()
        assert v.runtime_version == "22.0.0"
        assert v.immutable is True


class TestAuditVersionInfo:
    def test_immutable(self):
        v = AuditVersionInfo()
        with pytest.raises(FrozenInstanceError):
            v.version = "x"


class TestAuditHistory:
    def test_record(self):
        h = AuditHistoryRecorder().record(
            [AuditDescriptor("a", category="security")])
        assert h.size() == 1
        assert h.entries[0].category == "security"

    def test_immutable(self):
        h = AuditHistory()
        with pytest.raises(FrozenInstanceError):
            h.entries = ()


class TestAuditHistoryEntry:
    def test_immutable(self):
        e = AuditHistoryEntry("a")
        with pytest.raises(FrozenInstanceError):
            e.action = "x"


class TestConversationCatalogBridge:
    def test_5_queries(self):
        b = ConversationCatalogBridge(_catalog())
        assert b.query_1_count()["count"] == 2
        assert b.query_2_by_category("security")["count"] == 1
        assert b.query_3_index()["size"] == 2
        assert b.query_4_loader()["loaded"] is True
        assert b.query_5_version()["runtime_version"] == "22.0.0"


class TestDashboardCatalogBridge:
    def test_five_cards(self):
        b = DashboardCatalogBridge(_catalog())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_verdict(self):
        b = DashboardCatalogBridge(_catalog())
        assert b.verdict_card().status == "ready"


class TestCatalogImmutability:
    DTO_CLASSES = [
        AuditIndex, AuditLoadResult, AuditVersionInfo, AuditHistory,
        AuditHistoryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"


class TestNoDiskIO:
    def test_no_file_read(self):
        import inspect
        src = inspect.getsource(AuditLoader)
        assert "open(" not in src
        assert "pathlib" not in src
