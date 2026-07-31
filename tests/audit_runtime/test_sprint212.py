"""Sprint 212 — Audit Foundation Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.audit_runtime.foundation.audit_descriptor import AuditDescriptor
from sam.audit_runtime.foundation.audit_capability import AuditCapability
from sam.audit_runtime.foundation.audit_contract import AuditContract
from sam.audit_runtime.foundation.audit_metadata import AuditMetadata
from sam.audit_runtime.foundation.audit_registry import AuditRegistry
from sam.audit_runtime.foundation.conversation_audit import (
    ConversationAuditBridge,
)
from sam.audit_runtime.foundation.dashboard_audit import DashboardAuditBridge
from sam.audit_runtime.dashboard import PolicyCard


class TestAuditDescriptor:
    def test_defaults(self):
        d = AuditDescriptor("aud1")
        assert d.category == "general"
        assert d.provenance is True
        assert d.traceability is True

    def test_immutable(self):
        d = AuditDescriptor("aud1")
        with pytest.raises(FrozenInstanceError):
            d.category = "x"

    def test_empty_id(self):
        with pytest.raises(ValueError):
            AuditDescriptor("  ")

    def test_tags_tuple(self):
        d = AuditDescriptor("aud1", tags=["a", "b"])
        assert isinstance(d.tags, tuple)


class TestAuditCapability:
    def test_defaults(self):
        c = AuditCapability()
        assert c.immutable_record is True
        assert c.preview_only is True
        assert c.no_execute is True

    def test_immutable(self):
        c = AuditCapability()
        with pytest.raises(FrozenInstanceError):
            c.deterministic = False


class TestAuditContract:
    def test_guarantees(self):
        c = AuditContract()
        assert "immutable" in c.guarantees
        assert "no_write" in c.guarantees
        assert "deterministic" in c.guarantees

    def test_immutable(self):
        c = AuditContract()
        with pytest.raises(FrozenInstanceError):
            c.no_write = False


class TestAuditMetadata:
    def test_defaults(self):
        m = AuditMetadata()
        assert m.version == "22.0.0"
        assert m.runtime == "audit_runtime"
        assert m.phase == "XXII"
        assert m.immutable is True

    def test_immutable(self):
        m = AuditMetadata()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestAuditRegistry:
    def test_empty(self):
        r = AuditRegistry()
        assert r.count() == 0
        assert r.exists("x") is False

    def test_register(self):
        r = AuditRegistry()
        r2 = r.register(AuditDescriptor("aud1", category="security"))
        assert r2.count() == 1
        assert r2.exists("aud1") is True

    def test_get(self):
        r = AuditRegistry().register(
            AuditDescriptor("aud1", category="security"))
        assert r.get("aud1").category == "security"

    def test_all_entries(self):
        r = AuditRegistry().register(AuditDescriptor("a")).register(
            AuditDescriptor("b"))
        assert len(r.all_entries()) == 2


class TestConversationAuditBridge:
    def test_5_queries(self):
        r = AuditRegistry().register(AuditDescriptor("a", category="security"))
        b = ConversationAuditBridge(r)
        assert b.query_1_count()["count"] == 1
        assert b.query_2_exists("a")["exists"] is True
        assert b.query_3_empty()["empty"] is False
        assert b.query_4_categories()["categories"] == ["security"]
        assert b.query_5_immutable()["no_execute"] is True


class TestDashboardAuditBridge:
    def test_five_cards(self):
        b = DashboardAuditBridge(AuditRegistry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_verdict(self):
        b = DashboardAuditBridge(AuditRegistry())
        assert b.verdict_card().status == "immutable"


class TestPolicyCard:
    def test_immutable(self):
        c = PolicyCard("k", "audit", "ready")
        with pytest.raises(FrozenInstanceError):
            c.status = "x"


class TestFoundationImmutability:
    DTO_CLASSES = [
        AuditDescriptor, AuditCapability, AuditContract, AuditMetadata,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"


class TestNoWrite:
    def test_descriptor_is_value_object(self):
        d = AuditDescriptor("aud1")
        assert d.audit_id == "aud1"
