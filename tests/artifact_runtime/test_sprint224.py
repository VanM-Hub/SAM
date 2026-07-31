"""Sprint 224 — Artifact Catalog Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.artifact_runtime.catalog.artifact_catalog import ArtifactCatalog
from sam.artifact_runtime.catalog.artifact_index import (
    ArtifactIndex, ArtifactIndexer,
)
from sam.artifact_runtime.catalog.artifact_loader import (
    ArtifactLoader, ArtifactLoadResult,
)
from sam.artifact_runtime.catalog.artifact_version import (
    ArtifactVersionProvider, ArtifactVersionInfo,
)
from sam.artifact_runtime.catalog.artifact_history import (
    ArtifactHistory, ArtifactHistoryEntry, ArtifactRecorder,
)
from sam.artifact_runtime.catalog.conversation_catalog import (
    ConversationCatalogBridge,
)
from sam.artifact_runtime.catalog.dashboard_catalog import DashboardCatalogBridge
from sam.artifact_runtime.model.artifact import Artifact
from sam.artifact_runtime.dashboard import PolicyCard


class TestArtifactCatalog:
    def test_add_immutable(self):
        c0 = ArtifactCatalog()
        c1 = c0.add(Artifact("a", "report"))
        assert c0.count() == 0
        assert c1.count() == 1

    def test_get(self):
        c = ArtifactCatalog().add(Artifact("a", "report"))
        assert c.get("a").name == "a"
        assert c.get("x") is None

    def test_by_kind(self):
        c = ArtifactCatalog().add(Artifact("a", "report")).add(
            Artifact("b", "log")).add(Artifact("c", "report"))
        assert len(c.by_kind("report")) == 2
        assert len(c.by_kind("log")) == 1


class TestArtifactIndex:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactIndex().ids = ("a",)


class TestArtifactIndexer:
    def test_sort(self):
        idx = ArtifactIndexer().index(("c", "a", "b"))
        assert list(idx.ids) == ["a", "b", "c"]


class TestArtifactLoader:
    def test_no_file(self):
        res = ArtifactLoader().load((Artifact("a", "report"),))
        assert res.loaded == 1
        assert res.external_calls == 0
        assert res.catalog.count() == 1

    def test_empty(self):
        assert ArtifactLoader().load().loaded == 0


class TestArtifactLoadResult:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactLoadResult().loaded = 5


class TestArtifactVersionProvider:
    def test_version(self):
        v = ArtifactVersionProvider().version()
        assert v.version == "23.0.0"
        assert v.phase == "XXIII"


class TestArtifactVersionInfo:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactVersionInfo().version = "x"


class TestArtifactHistory:
    def test_record_in_memory(self):
        h = ArtifactHistory().record(ArtifactHistoryEntry("a"))
        assert h.count() == 1

    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactHistoryEntry().name = "x"


class TestArtifactRecorder:
    def test_append(self):
        r = ArtifactRecorder()
        assert r.append("a").count() == 1


class TestConversationCatalogBridge:
    def test_five_queries(self):
        b = ConversationCatalogBridge()
        assert b.query_1_count() == 1
        assert b.query_2_lookup("out")["found"] is True
        assert b.query_3_loader()["external_calls"] == 0
        assert b.query_4_history()["count"] == 1
        assert b.query_5_version()["version"] == "23.0.0"


class TestDashboardCatalogBridge:
    def test_five_cards(self):
        cards = DashboardCatalogBridge().cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)


class TestCatalogImmutability:
    DTO = [ArtifactIndex, ArtifactLoadResult, ArtifactVersionInfo,
           ArtifactHistoryEntry]

    def test_all_frozen(self):
        for cls in self.DTO:
            assert cls.__dataclass_params__.frozen
