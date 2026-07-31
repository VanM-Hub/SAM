"""Sprint 118 — Connector Translation Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.connectors.translation_request import TranslationRequest
from sam.connectors.translation_result import TranslationResult
from sam.connectors.translation_engine import TranslationEngine
from sam.connectors.translation_validator import (
    TranslationValidator, TranslationValidationReport,
)
from sam.connectors.translation_summary import TranslationSummary, TranslationSummarizer
from sam.connectors.conversation_translation import ConversationTranslationBridge
from sam.connectors.dashboard_translation import DashboardTranslationBridge
from sam.connectors.dashboard_connector import ExecutionCard


# ============================================================
# DTO
# ============================================================
class TestTranslationRequest:
    def test_create(self):
        r = TranslationRequest("t1", "c1", "sam", {"id": "x"})
        assert r.request_id == "t1"

    def test_defaults(self):
        r = TranslationRequest("t1", "c1")
        assert r.source_schema == "sam"
        assert r.payload == {}

    def test_immutable(self):
        r = TranslationRequest("t1", "c1")
        with pytest.raises(FrozenInstanceError):
            r.payload = {"x": 1}


class TestTranslationResult:
    def test_create(self):
        r = TranslationResult("t1", "c1", True, {"schema": "neutral"}, "neutral")
        assert r.success is True

    def test_defaults(self):
        r = TranslationResult("t1", "c1")
        assert r.success is False
        assert r.target_schema == "neutral"

    def test_immutable(self):
        r = TranslationResult("t1", "c1")
        with pytest.raises(FrozenInstanceError):
            r.success = True


# ============================================================
# Engine — TranslationEngine
# ============================================================
class TestTranslationEngine:
    def test_translate(self):
        e = TranslationEngine()
        res = e.translate(TranslationRequest("t1", "c1", payload={
            "id": "abc", "name": "Test", "value": 42, "unknown_key": 1,
        }))
        assert res.success is True
        assert res.neutral_payload["schema"] == "sam.neutral.v1"
        fields = res.neutral_payload["fields"]
        # hanya key yang dikenali (id, name, value) — unknown_key di-skip
        keys = {f["key"] for f in fields}
        assert "id" in keys and "name" in keys and "value" in keys
        assert "unknown_key" not in keys

    def test_type_inference(self):
        e = TranslationEngine()
        res = e.translate(TranslationRequest("t1", "c1", payload={
            "id": "x", "value": 3.14, "status": True, "message": "hi",
        }))
        types = {f["key"]: f["type"] for f in res.neutral_payload["fields"]}
        assert types["value"] == "number"
        assert types["status"] == "boolean"

    def test_empty_payload_fields(self):
        e = TranslationEngine()
        res = e.translate(TranslationRequest("t1", "c1"))
        assert res.neutral_payload["fields"] == []


# ============================================================
# Engine — TranslationValidator
# ============================================================
class TestTranslationValidator:
    def test_valid(self):
        v = TranslationValidator()
        report = v.validate(TranslationRequest("t1", "c1", payload={"id": "x"}))
        assert report.valid is True

    def test_empty_payload(self):
        v = TranslationValidator()
        report = v.validate(TranslationRequest("t1", "c1"))
        assert report.valid is False
        assert any("payload" in i for i in report.issues)


# ============================================================
# Engine — TranslationSummarizer
# ============================================================
class TestTranslationSummarizer:
    def test_summary(self):
        s = TranslationSummarizer().summarize([
            TranslationResult("a", "c1", True),
            TranslationResult("b", "c1", False),
        ])
        assert s.total == 2
        assert s.success == 1
        assert s.failures == 1


# ============================================================
# Bridges
# ============================================================
class TestConversationTranslationBridge:
    def test_translate(self):
        b = ConversationTranslationBridge()
        res = b.translate(TranslationRequest("t1", "c1", payload={"id": "x"}))
        assert res.success is True


class TestDashboardTranslationBridge:
    def test_five_cards(self):
        b = DashboardTranslationBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)


# ============================================================
# Immutability
# ============================================================
class TestTranslationImmutability:
    DTO_CLASSES = [
        TranslationRequest, TranslationResult,
        TranslationValidationReport, TranslationSummary,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
