"""Sprint 149 — OpenClaw Provider Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.providers.openclaw.openclaw_provider import OpenClawProvider
from sam.providers.openclaw.tool_request import OpenClawToolRequest
from sam.providers.openclaw.tool_registry import OpenClawToolRegistry, ToolDefinition
from sam.providers.openclaw.tool_validator import OpenClawToolValidator, OpenClawToolValidation
from sam.providers.openclaw.tool_preview import OpenClawToolPreview, OpenClawToolPreviewEngine
from sam.providers.openclaw.tool_history import OpenClawToolHistory, OpenClawHistoryEntry
from sam.providers.openclaw.conversation_openclaw import ConversationOpenClawBridge
from sam.providers.openclaw.dashboard_openclaw import DashboardOpenClawBridge
from sam.providers.base.base_provider import ProviderError
from sam.providers.dashboard.dashboard_provider import ExecutionCard


class TestOpenClawProvider:
    def test_descriptor(self):
        p = OpenClawProvider()
        assert p.descriptor.provider_type == "openclaw"

    def test_build_tool(self):
        p = OpenClawProvider()
        r = p.build_tool("search", {"q": "x"})
        assert r["preview"] is True
        assert r["invoked"] is False
        assert r["external_calls"] == 0
        assert r["arguments"] == {"q": "x"}

    def test_build_empty_raises(self):
        with pytest.raises(ProviderError):
            OpenClawProvider().build_tool("")

    def test_external_always_zero(self):
        p = OpenClawProvider()
        p.build_tool("search")
        assert p.external_calls == 0


class TestOpenClawToolRequest:
    def test_valid(self):
        r = OpenClawToolRequest("r1", "search", {"q": "a"})
        assert r.is_valid() is True

    def test_immutable(self):
        r = OpenClawToolRequest("r1", "search")
        with pytest.raises(FrozenInstanceError):
            r.tool = "other"


class TestOpenClawToolRegistry:
    def test_add_get(self):
        reg = OpenClawToolRegistry()
        assert reg.add(ToolDefinition("search")) is True
        assert reg.get("search").name == "search"

    def test_duplicate_rejected(self):
        reg = OpenClawToolRegistry()
        reg.add(ToolDefinition("search"))
        assert reg.add(ToolDefinition("search")) is False

    def test_has_count(self):
        reg = OpenClawToolRegistry()
        reg.add(ToolDefinition("search"))
        reg.add(ToolDefinition("read"))
        assert reg.count() == 2
        assert reg.has("search")
        assert not reg.has("missing")

    def test_def_preview_only(self):
        assert ToolDefinition("x").preview_only is True


class TestOpenClawToolValidator:
    def test_valid(self):
        v = OpenClawToolValidator().validate(OpenClawToolRequest("r1", "search"))
        assert v.valid is True

    def test_invalid(self):
        v = OpenClawToolValidator().validate(OpenClawToolRequest("", ""))
        assert v.valid is False


class TestOpenClawToolPreviewEngine:
    def test_preview(self):
        p = OpenClawToolPreviewEngine().preview(OpenClawToolRequest("r1", "search"))
        assert p.invoked is False
        assert p.external_calls == 0


class TestOpenClawToolHistory:
    def test_record(self):
        h = OpenClawToolHistory()
        h.record(OpenClawHistoryEntry("r1", "search"))
        assert h.count() == 1

    def test_no_invoke(self):
        h = OpenClawToolHistory()
        h.record(OpenClawHistoryEntry("r1", "search"))
        assert h.total_external_calls() == 0


class TestConversationOpenClawBridge:
    def test_describe(self):
        b = ConversationOpenClawBridge(OpenClawProvider())
        assert "openclaw" in b.describe()

    def test_contract(self):
        b = ConversationOpenClawBridge(OpenClawProvider())
        assert "openclaw" in b.contract()

    def test_supports(self):
        b = ConversationOpenClawBridge(OpenClawProvider())
        assert b.supports("tool_build")


class TestDashboardOpenClawBridge:
    def test_card(self):
        b = DashboardOpenClawBridge(OpenClawProvider())
        card = b.card()
        assert isinstance(card, ExecutionCard)
        assert card.provider_id == "openclaw"
        assert card.verdict == "ready"


class TestOpenClawImmutability:
    DTO_CLASSES = [
        OpenClawToolRequest, ToolDefinition,
        OpenClawToolValidation, OpenClawToolPreview, OpenClawHistoryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
