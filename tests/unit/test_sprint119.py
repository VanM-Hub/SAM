"""Sprint 119 — Connector Preview Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.connectors.connector_descriptor import ConnectorDescriptor
from sam.connectors.connector_capability import ConnectorCapability
from sam.connectors.connector_registry import ConnectorRegistry
from sam.connectors.preview_request import PreviewRequest
from sam.connectors.preview_result import PreviewResult
from sam.connectors.preview_validator import PreviewValidator, PreviewValidationReport
from sam.connectors.preview_engine import PreviewEngine
from sam.connectors.preview_report import PreviewReport, PreviewReporter
from sam.connectors.preview_history import PreviewHistory, PreviewHistoryEntry
from sam.connectors.conversation_preview import ConversationPreviewBridge
from sam.connectors.dashboard_preview import DashboardPreviewBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _make_registry():
    r = ConnectorRegistry()
    r.register(ConnectorDescriptor("c1", "OpenAI", "llm"))
    r.attach_capability(ConnectorCapability("cap1", "c1", "generate", "llm"))
    return r


# ============================================================
# DTO
# ============================================================
class TestPreviewRequest:
    def test_create(self):
        r = PreviewRequest("p1", "c1", "read")
        assert r.dry_run is True  # default always True

    def test_immutable(self):
        r = PreviewRequest("p1", "c1")
        with pytest.raises(FrozenInstanceError):
            r.operation = "write"


class TestPreviewResult:
    def test_default_external_calls_zero(self):
        r = PreviewResult("p1", "c1", "read", True)
        assert r.external_calls == 0

    def test_immutable(self):
        r = PreviewResult("p1", "c1")
        with pytest.raises(FrozenInstanceError):
            r.success = True


# ============================================================
# Engine — PreviewEngine (no external call guarantee)
# ============================================================
class TestPreviewEngine:
    def test_preview_success(self):
        e = PreviewEngine(_make_registry())
        res = e.preview(PreviewRequest("p1", "c1", "read"))
        assert res.success is True
        assert res.external_calls == 0
        assert any("dry-run" in x for x in res.simulated_effects)

    def test_preview_unknown_connector(self):
        e = PreviewEngine(_make_registry())
        res = e.preview(PreviewRequest("p1", "ghost", "read"))
        assert res.success is False
        assert res.external_calls == 0


# ============================================================
# Engine — PreviewValidator
# ============================================================
class TestPreviewValidator:
    def test_valid(self):
        v = PreviewValidator()
        report = v.validate(PreviewRequest("p1", "c1", "read"))
        assert report.valid is True

    def test_non_dry_run_flagged(self):
        v = PreviewValidator()
        req = PreviewRequest("p1", "c1", "read")
        # ganti dry_run via object baru (immutable)
        req2 = PreviewRequest("p1", "c1", "read", dry_run=False)
        report = v.validate(req2)
        assert report.valid is False

    def test_unknown_operation(self):
        v = PreviewValidator()
        report = v.validate(PreviewRequest("p1", "c1", "delete"))
        assert report.valid is False


# ============================================================
# Engine — PreviewReporter / PreviewHistory
# ============================================================
class TestPreviewReporter:
    def test_report(self):
        r = PreviewReporter().report([
            PreviewResult("p1", "c1", "read", True, [], 0),
            PreviewResult("p2", "c1", "read", False, [], 0),
        ])
        assert r.successes == 1
        assert r.failures == 1
        assert r.total_external_calls == 0


class TestPreviewHistory:
    def test_record_and_count(self):
        h = PreviewHistory()
        h.record(PreviewResult("p1", "c1", "read", True))
        assert h.count() == 1

    def test_entry_immutable(self):
        h = PreviewHistory()
        with pytest.raises(FrozenInstanceError):
            PreviewHistoryEntry("p1", "c1").__setattr__("success", True)


# ============================================================
# Bridge — conversation preview memaksa dry_run
# ============================================================
class TestConversationPreviewBridge:
    def test_forces_dry_run(self):
        b = ConversationPreviewBridge(_make_registry())
        req = PreviewRequest("p1", "c1", "read", dry_run=False)
        res = b.preview(req)
        # bridge memaksa dry_run = True
        assert res.external_calls == 0


class TestDashboardPreviewBridge:
    def test_five_cards(self):
        b = DashboardPreviewBridge(_make_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)


# ============================================================
# Immutability
# ============================================================
class TestPreviewImmutability:
    DTO_CLASSES = [
        PreviewRequest, PreviewResult, PreviewValidationReport,
        PreviewReport, PreviewHistoryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
