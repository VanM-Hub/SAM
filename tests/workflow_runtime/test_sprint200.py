"""Sprint 200 — Workflow Catalog Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.workflow_runtime.catalog.workflow_catalog import (
    WorkflowCatalog, WorkflowCatalogEntry,
)
from sam.workflow_runtime.catalog.workflow_index import WorkflowIndex, WorkflowIndexer
from sam.workflow_runtime.catalog.workflow_loader import (
    WorkflowLoader, WorkflowLoadResult,
)
from sam.workflow_runtime.catalog.workflow_version import (
    WorkflowVersionInfo, WorkflowVersionProvider,
)
from sam.workflow_runtime.catalog.workflow_history import (
    WorkflowHistory, WorkflowHistoryEntry,
)
from sam.workflow_runtime.catalog.conversation_catalog import ConversationCatalogBridge
from sam.workflow_runtime.catalog.dashboard_catalog import DashboardCatalogBridge
from sam.workflow_runtime.model.workflow import Workflow
from sam.workflow_runtime.model.workflow_step import WorkflowStep
from sam.workflow_runtime.dashboard import WorkflowCard


def _wf():
    return Workflow("w1", steps=["s1", "s2"])


class TestWorkflowCatalog:
    def test_add_get(self):
        c = WorkflowCatalog()
        c.add(_wf())
        assert c.get("w1").workflow_id == "w1"

    def test_count(self):
        c = WorkflowCatalog()
        c.add(_wf())
        assert c.count() == 1

    def test_all_entries(self):
        c = WorkflowCatalog()
        c.add(_wf())
        entries = c.all_entries()
        assert len(entries) == 1
        assert entries[0].step_count == 2

    def test_by_scope(self):
        c = WorkflowCatalog()
        c.add(_wf())
        c.add(Workflow("w2", scope="decision"))
        assert len(c.by_scope("process")) == 1

    def test_missing_get(self):
        assert WorkflowCatalog().get("nope") is None

    def test_no_file_load(self):
        # catalog murni in-memory, tidak ada disk read
        assert WorkflowCatalog().count() == 0


class TestWorkflowCatalogEntry:
    def test_immutable(self):
        e = WorkflowCatalogEntry("w")
        with pytest.raises(FrozenInstanceError):
            e.step_count = 1


class TestWorkflowIndexer:
    def test_index(self):
        wf = _wf()
        steps = [WorkflowStep("s1", "w1"), WorkflowStep("s2", "w1")]
        idx = WorkflowIndexer().index(wf, steps)
        assert idx.step_count == 2
        assert idx.has_step("s1") is True

    def test_search(self):
        wf = _wf()
        steps = [WorkflowStep("s1", "w1"), WorkflowStep("s2", "w1")]
        idx = WorkflowIndexer().index(wf, steps)
        results = WorkflowIndexer().search(idx, "s")
        assert len(results) == 2


class TestWorkflowIndex:
    def test_default(self):
        assert WorkflowIndex().step_count == 0

    def test_immutable(self):
        idx = WorkflowIndex()
        with pytest.raises(FrozenInstanceError):
            idx.step_count = 1


class TestWorkflowLoader:
    def test_load_found(self):
        c = WorkflowCatalog()
        c.add(_wf())
        r = WorkflowLoader(c).load("w1")
        assert r.ok is True
        assert r.workflow.workflow_id == "w1"

    def test_load_missing(self):
        r = WorkflowLoader(WorkflowCatalog()).load("nope")
        assert r.ok is False
        assert r.detail == "not found"


class TestWorkflowLoadResult:
    def test_default(self):
        assert WorkflowLoadResult().ok is False

    def test_immutable(self):
        r = WorkflowLoadResult()
        with pytest.raises(FrozenInstanceError):
            r.ok = True


class TestWorkflowVersionProvider:
    def test_provide(self):
        v = WorkflowVersionProvider().provide("w1")
        assert v.version == "20.0.0"
        assert v.workflow_id == "w1"


class TestWorkflowVersionInfo:
    def test_immutable(self):
        v = WorkflowVersionInfo()
        with pytest.raises(FrozenInstanceError):
            v.version = "x"


class TestWorkflowHistory:
    def test_record_and_count(self):
        h = WorkflowHistory()
        h.record(WorkflowHistoryEntry("w1", "created"))
        assert h.count() == 1

    def test_by_workflow(self):
        h = WorkflowHistory()
        h.record(WorkflowHistoryEntry("w1"))
        h.record(WorkflowHistoryEntry("w2"))
        assert len(h.by_workflow("w1")) == 1

    def test_default_action(self):
        e = WorkflowHistoryEntry("w1")
        assert e.action == "created"


class TestConversationCatalogBridge:
    def test_5_queries(self):
        b = ConversationCatalogBridge()
        wf = _wf()
        assert b.query_1_add(wf)["added"] == "w1"
        assert b.query_2_load("w1")["ok"] is True
        assert b.query_3_search("w1", "s") == []
        assert b.query_4_version("w1")["version"] == "20.0.0"
        assert b.query_5_history("w1") == ["w1"]

    def test_search_missing(self):
        assert ConversationCatalogBridge().query_3_search("nope", "x") == []


class TestDashboardCatalogBridge:
    def test_five_cards(self):
        b = DashboardCatalogBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, WorkflowCard) for c in cards)

    def test_overview(self):
        b = DashboardCatalogBridge()
        assert b.overview_card().group == "catalog"


class TestCatalogImmutability:
    DTO_CLASSES = [
        WorkflowCatalogEntry, WorkflowIndex, WorkflowLoadResult,
        WorkflowVersionInfo, WorkflowHistoryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
