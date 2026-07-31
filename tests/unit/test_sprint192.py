"""Sprint 192 — Cognitive Workspace Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.cognitive_runtime.workspace.cognitive_workspace import CognitiveWorkspace
from sam.cognitive_runtime.workspace.workspace_catalog import (
    WorkspaceCatalog, WorkspaceCatalogEntry,
)
from sam.cognitive_runtime.workspace.workspace_index import WorkspaceIndex, WorkspaceIndexer
from sam.cognitive_runtime.workspace.workspace_loader import (
    WorkspaceLoader, WorkspaceLoadResult,
)
from sam.cognitive_runtime.workspace.workspace_history import (
    WorkspaceHistory, WorkspaceHistoryEntry,
)
from sam.cognitive_runtime.workspace.conversation_workspace import ConversationWorkspaceBridge
from sam.cognitive_runtime.workspace.dashboard_workspace import DashboardWorkspaceBridge
from sam.cognitive_runtime.dashboard import ExecutionCard


def _ws():
    return CognitiveWorkspace("w1", items=["mission:1", "knowledge:k1"])


class TestCognitiveWorkspace:
    def test_basic(self):
        ws = _ws()
        assert ws.workspace_id == "w1"
        assert ws.item_count() == 2

    def test_preview_only(self):
        assert _ws().preview_only is True

    def test_immutable(self):
        ws = _ws()
        with pytest.raises(FrozenInstanceError):
            ws.items = ["x"]


class TestWorkspaceCatalog:
    def test_add_get(self):
        c = WorkspaceCatalog()
        ws = _ws()
        c.add(ws)
        assert c.get("w1").workspace_id == "w1"

    def test_count(self):
        c = WorkspaceCatalog()
        c.add(_ws())
        assert c.count() == 1

    def test_all_entries(self):
        c = WorkspaceCatalog()
        c.add(_ws())
        entries = c.all_entries()
        assert len(entries) == 1
        assert entries[0].item_count == 2

    def test_missing_get(self):
        assert WorkspaceCatalog().get("nope") is None


class TestWorkspaceCatalogEntry:
    def test_immutable(self):
        e = WorkspaceCatalogEntry("w")
        with pytest.raises(FrozenInstanceError):
            e.item_count = 1


class TestWorkspaceIndexer:
    def test_index(self):
        idx = WorkspaceIndexer().index(_ws())
        assert idx.item_count == 2
        assert idx.workspace_id == "w1"

    def test_has(self):
        idx = WorkspaceIndexer().index(_ws())
        assert idx.has("knowledge:k1") is True
        assert idx.has("nope") is False

    def test_search(self):
        idx = WorkspaceIndexer().index(_ws())
        results = WorkspaceIndexer().search(idx, "knowledge")
        assert results == ["knowledge:k1"]


class TestWorkspaceIndex:
    def test_default(self):
        assert WorkspaceIndex().item_count == 0

    def test_immutable(self):
        idx = WorkspaceIndex()
        with pytest.raises(FrozenInstanceError):
            idx.item_count = 1


class TestWorkspaceLoader:
    def test_load_found(self):
        c = WorkspaceCatalog()
        c.add(_ws())
        r = WorkspaceLoader(c).load("w1")
        assert r.ok is True
        assert r.workspace.workspace_id == "w1"

    def test_load_missing(self):
        r = WorkspaceLoader(WorkspaceCatalog()).load("nope")
        assert r.ok is False
        assert r.detail == "not found"


class TestWorkspaceLoadResult:
    def test_default(self):
        assert WorkspaceLoadResult().ok is False

    def test_immutable(self):
        r = WorkspaceLoadResult()
        with pytest.raises(FrozenInstanceError):
            r.ok = True


class TestWorkspaceHistory:
    def test_record_and_count(self):
        h = WorkspaceHistory()
        h.record(WorkspaceHistoryEntry("w1", "created"))
        assert h.count() == 1

    def test_by_workspace(self):
        h = WorkspaceHistory()
        h.record(WorkspaceHistoryEntry("w1"))
        h.record(WorkspaceHistoryEntry("w2"))
        assert len(h.by_workspace("w1")) == 1

    def test_default_action(self):
        e = WorkspaceHistoryEntry("w1")
        assert e.action == "created"


class TestConversationWorkspaceBridge:
    def test_5_queries(self):
        b = ConversationWorkspaceBridge()
        ws = _ws()
        assert b.query_1_add(ws)["added"] == "w1"
        assert b.query_2_load("w1")["ok"] is True
        assert b.query_3_index("w1")["item_count"] == 2
        assert b.query_4_search("w1", "knowledge") == ["knowledge:k1"]
        assert b.query_5_history("w1") == ["w1"]

    def test_search_missing(self):
        assert ConversationWorkspaceBridge().query_4_search("nope", "x") == []


class TestDashboardWorkspaceBridge:
    def test_five_cards(self):
        b = DashboardWorkspaceBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardWorkspaceBridge()
        assert b.overview_card().group == "workspace"


class TestWorkspaceImmutability:
    DTO_CLASSES = [
        CognitiveWorkspace, WorkspaceCatalogEntry, WorkspaceIndex,
        WorkspaceLoadResult, WorkspaceHistoryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
