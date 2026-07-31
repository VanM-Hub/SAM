"""Sprint 145 — Filesystem Provider Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.providers.filesystem.filesystem_provider import FilesystemProvider, FILESYSTEM_OPERATIONS
from sam.providers.filesystem.filesystem_request import FilesystemRequest
from sam.providers.filesystem.filesystem_response import FilesystemResponse
from sam.providers.filesystem.filesystem_validator import FilesystemValidator, FilesystemValidation
from sam.providers.filesystem.filesystem_history import FilesystemHistory, FilesystemHistoryEntry
from sam.providers.filesystem.conversation_filesystem import ConversationFilesystemBridge
from sam.providers.filesystem.dashboard_filesystem import DashboardFilesystemBridge
from sam.providers.base.base_provider import ProviderError
from sam.providers.dashboard.dashboard_provider import ExecutionCard


class TestFilesystemProvider:
    def test_descriptor(self):
        p = FilesystemProvider()
        assert p.descriptor.provider_type == "filesystem"
        assert "filesystem" in p.descriptor.implements[0]

    def test_operations(self):
        p = FilesystemProvider()
        for op in ["read", "write", "copy", "move", "delete",
                   "exists", "list", "mkdir", "preview"]:
            assert p.supports(op), f"should support {op}"

    def test_frozen_operations(self):
        assert FILESYSTEM_OPERATIONS == [
            "read", "write", "copy", "move", "delete",
            "exists", "list", "mkdir", "preview",
        ]

    def test_preview_read(self):
        p = FilesystemProvider()
        r = p.preview_operation("read", {"path": "/tmp/a.txt"})
        assert r["preview"] is True
        assert r["external_calls"] == 0
        assert r["dry_run"] is True

    def test_preview_requires_path(self):
        with pytest.raises(ProviderError):
            FilesystemProvider().preview_operation("read", {})

    def test_preview_unsupported(self):
        with pytest.raises(ProviderError):
            FilesystemProvider().preview_operation("rename", {"path": "/x"})

    def test_external_calls_always_zero(self):
        p = FilesystemProvider()
        p.preview_operation("read", {"path": "/x"})
        p.preview_operation("write", {"path": "/x", "content": "hi"})
        assert p.external_calls == 0


class TestFilesystemRequest:
    def test_default(self):
        r = FilesystemRequest("r1", "read", "/tmp/a")
        assert r.is_valid() is True
        assert r.recursive is False

    def test_copy_valid(self):
        r = FilesystemRequest("r1", "copy", "/a", target_path="/b")
        assert r.is_valid() is True

    def test_immutable(self):
        r = FilesystemRequest("r1", "read", "/a")
        with pytest.raises(FrozenInstanceError):
            r.path = "/b"


class TestFilesystemResponse:
    def test_default(self):
        r = FilesystemResponse("r1", "read")
        assert r.preview is True
        assert r.external_calls == 0

    def test_immutable(self):
        r = FilesystemResponse("r1", "read")
        with pytest.raises(FrozenInstanceError):
            r.ok = False


class TestFilesystemValidator:
    def test_valid_read(self):
        v = FilesystemValidator().validate(FilesystemRequest("r1", "read", "/a"))
        assert v.valid is True

    def test_copy_without_target(self):
        v = FilesystemValidator().validate(FilesystemRequest("r1", "copy", "/a"))
        assert v.valid is False

    def test_unsupported_op(self):
        v = FilesystemValidator().validate(FilesystemRequest("r1", "rename", "/a"))
        assert v.valid is False

    def test_missing_path(self):
        v = FilesystemValidator().validate(FilesystemRequest("r1", "read", ""))
        assert v.valid is False


class TestFilesystemHistory:
    def test_record(self):
        h = FilesystemHistory()
        h.record(FilesystemHistoryEntry("r1", "read", "/a", ok=True, external_calls=0))
        assert h.count() == 1

    def test_no_external(self):
        h = FilesystemHistory()
        h.record(FilesystemHistoryEntry("r1", "read", "/a"))
        assert h.total_external_calls() == 0


class TestConversationFilesystemBridge:
    def test_describe(self):
        b = ConversationFilesystemBridge(FilesystemProvider())
        assert "filesystem" in b.describe()

    def test_operations(self):
        b = ConversationFilesystemBridge(FilesystemProvider())
        assert len(b.operations()) == 9

    def test_supports(self):
        b = ConversationFilesystemBridge(FilesystemProvider())
        assert b.supports("read")
        assert not b.supports("rename")


class TestDashboardFilesystemBridge:
    def test_card(self):
        b = DashboardFilesystemBridge(FilesystemProvider())
        card = b.card()
        assert isinstance(card, ExecutionCard)
        assert card.provider_id == "filesystem"
        assert card.verdict == "ready"

    def test_detail_card(self):
        b = DashboardFilesystemBridge(FilesystemProvider())
        assert b.detail_card().provider_type == "filesystem"


class TestFilesystemImmutability:
    DTO_CLASSES = [
        FilesystemRequest, FilesystemResponse,
        FilesystemValidation, FilesystemHistoryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
