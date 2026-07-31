"""Sprint 114 — Connector Capability Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.connectors.connector_descriptor import ConnectorDescriptor
from sam.connectors.connector_capability import ConnectorCapability
from sam.connectors.connector_registry import ConnectorRegistry
from sam.connectors.capability_profile import CapabilityProfile
from sam.connectors.capability_matrix import (
    CapabilityMatrixEntry, CapabilityMatrix, CapabilityMatrixBuilder,
)
from sam.connectors.capability_validator import (
    CapabilityValidator, CapabilityValidationIssue, CapabilityValidationReport,
)
from sam.connectors.capability_selector import CapabilitySelector, CapabilitySelection
from sam.connectors.capability_report import CapabilityReport, CapabilityReporter
from sam.connectors.conversation_capability import ConversationCapabilityBridge
from sam.connectors.dashboard_capability import DashboardCapabilityBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _make_registry():
    r = ConnectorRegistry()
    r.register(ConnectorDescriptor("c1", "OpenAI", "llm"))
    r.register(ConnectorDescriptor("c2", "Postgres", "db"))
    r.attach_capability(ConnectorCapability("cap1", "c1", "generate", "llm", supported_operations=["gen"]))
    r.attach_capability(ConnectorCapability("cap2", "c1", "embed", "llm", supported_operations=["emb"]))
    r.attach_capability(ConnectorCapability("cap3", "c2", "query", "db", supported_operations=["q"]))
    return r


# ============================================================
# DTO — CapabilityProfile
# ============================================================
class TestCapabilityProfile:
    def test_create(self):
        p = CapabilityProfile("p1", "c1", ["cap1"], "llm", 0.8)
        assert p.profile_id == "p1"
        assert p.strength == 0.8

    def test_defaults(self):
        p = CapabilityProfile("p1", "c1")
        assert p.capability_ids == []
        assert p.category == "generic"
        assert p.strength == 0.0

    def test_immutable(self):
        p = CapabilityProfile("p1", "c1")
        with pytest.raises(FrozenInstanceError):
            p.strength = 0.5


# ============================================================
# DTO — CapabilityMatrix
# ============================================================
class TestCapabilityMatrixEntry:
    def test_create(self):
        e = CapabilityMatrixEntry("c1", "generate", "full", 1)
        assert e.support_level == "full"

    def test_immutable(self):
        e = CapabilityMatrixEntry("c1", "gen")
        with pytest.raises(FrozenInstanceError):
            e.count = 2


class TestCapabilityMatrix:
    def test_by_connector(self):
        m = CapabilityMatrix(entries=[
            CapabilityMatrixEntry("c1", "a"), CapabilityMatrixEntry("c2", "b"),
            CapabilityMatrixEntry("c1", "c"),
        ])
        assert len(m.by_connector("c1")) == 2

    def test_immutable(self):
        m = CapabilityMatrix()
        with pytest.raises(FrozenInstanceError):
            m.entries = []


class TestCapabilityMatrixBuilder:
    def test_build(self):
        b = CapabilityMatrixBuilder(_make_registry())
        m = b.build()
        # c1 punya 2, c2 punya 1
        assert len(m.by_connector("c1")) == 2
        assert len(m.by_connector("c2")) == 1


# ============================================================
# Engine — CapabilityValidator
# ============================================================
class TestCapabilityValidator:
    def test_valid(self):
        v = CapabilityValidator(_make_registry())
        report = v.validate("c1")
        assert report.valid is True

    def test_empty_capability_flagged(self):
        r = ConnectorRegistry()
        r.register(ConnectorDescriptor("c1", "X"))
        r.attach_capability(ConnectorCapability("", "c1", "gen"))
        v = CapabilityValidator(r)
        report = v.validate("c1")
        assert report.valid is False
        assert any(i.severity == "error" for i in report.issues)


# ============================================================
# Engine — CapabilitySelector
# ============================================================
class TestCapabilitySelector:
    def test_select(self):
        s = CapabilitySelector(_make_registry())
        sel = s.select("generate")
        assert sel.count == 1
        assert sel.selected_connectors == ["c1"]

    def test_select_none(self):
        s = CapabilitySelector(_make_registry())
        sel = s.select("stream")
        assert sel.count == 0


# ============================================================
# Engine — CapabilityReporter
# ============================================================
class TestCapabilityReporter:
    def test_report(self):
        rep = CapabilityReporter(_make_registry())
        r = rep.report("c1")
        assert r.total_capabilities == 2
        assert "generate" in r.capability_names

    def test_report_empty(self):
        rep = CapabilityReporter(_make_registry())
        r = rep.report("ghost")  # tidak terdaftar -> kosong
        assert r.total_capabilities == 0


# ============================================================
# Bridges
# ============================================================
class TestConversationCapabilityBridge:
    def test_get_report(self):
        b = ConversationCapabilityBridge(_make_registry())
        r = b.get_report("c1")
        assert r.total_capabilities == 2

    def test_matrix(self):
        b = ConversationCapabilityBridge(_make_registry())
        m = b.matrix()
        assert len(m.by_connector("c1")) == 2

    def test_list_capabilities(self):
        b = ConversationCapabilityBridge(_make_registry())
        assert b.list_capabilities("c1") == ["generate", "embed"]


class TestDashboardCapabilityBridge:
    def test_five_cards(self):
        b = DashboardCapabilityBridge(_make_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)


# ============================================================
# Immutability
# ============================================================
class TestCapabilityImmutability:
    DTO_CLASSES = [
        CapabilityProfile, CapabilityMatrixEntry, CapabilityMatrix,
        CapabilityValidationIssue, CapabilityValidationReport,
        CapabilitySelection, CapabilityReport,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
