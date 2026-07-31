"""Sprint 122 — Connector Certification Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.connectors.connector_descriptor import ConnectorDescriptor
from sam.connectors.connector_capability import ConnectorCapability
from sam.connectors.connector_registry import ConnectorRegistry
from sam.connectors.connector_certification import (
    CertificationCriterion, CertificationResult, ConnectorCertifier,
)
from sam.connectors.connector_score import ConnectorScore, ConnectorScorer
from sam.connectors.certification_validator import CertificationValidation, CertificationValidator
from sam.connectors.connector_report import ConnectorReport, ConnectorReporter
from sam.connectors.connector_manifest import ConnectorManifest
from sam.connectors.conversation_certification import ConversationCertificationBridge
from sam.connectors.dashboard_certification import DashboardCertificationBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _ready_registry():
    r = ConnectorRegistry()
    r.register(ConnectorDescriptor("c1", "OpenAI", "llm"))
    r.attach_capability(ConnectorCapability("cap1", "c1", "generate", "llm"))
    return r


# ============================================================
# DTO
# ============================================================
class TestCertificationCriterion:
    def test_default(self):
        c = CertificationCriterion("has_connectors")
        assert c.passed is False

    def test_immutable(self):
        c = CertificationCriterion("reg")
        with pytest.raises(FrozenInstanceError):
            c.passed = True


class TestCertificationResult:
    def test_immutable(self):
        r = CertificationResult()
        with pytest.raises(FrozenInstanceError):
            r.certified = True


class TestConnectorScore:
    def test_default(self):
        s = ConnectorScore("c1")
        assert s.score == 0.0

    def test_immutable(self):
        s = ConnectorScore("c1")
        with pytest.raises(FrozenInstanceError):
            s.score = 90.0


# ============================================================
# Engine — ConnectorCertifier
# ============================================================
class TestConnectorCertifier:
    def test_certified(self):
        c = ConnectorCertifier(_ready_registry())
        result = c.certify()
        assert result.certified is True
        assert result.score == 100.0

    def test_not_certified_empty(self):
        c = ConnectorCertifier(ConnectorRegistry())
        result = c.certify()
        assert result.certified is False
        assert result.score == 0.0


# ============================================================
# Engine — ConnectorScorer
# ============================================================
class TestConnectorScorer:
    def test_score(self):
        s = ConnectorScorer(_ready_registry())
        score = s.score("c1")
        assert score.score > 0
        assert "capability" in score.dimensions


# ============================================================
# Engine — CertificationValidator
# ============================================================
class TestCertificationValidator:
    def test_valid(self):
        v = CertificationValidator()
        result = ConnectorCertifier(_ready_registry()).certify()
        assert v.validate(result).valid is True


# ============================================================
# Engine — ConnectorReporter
# ============================================================
class TestConnectorReporter:
    def test_report_certified(self):
        rep = ConnectorReporter()
        r = rep.report(ConnectorCertifier(_ready_registry()).certify())
        assert r.certified is True


# ============================================================
# DTO — ConnectorManifest
# ============================================================
class TestConnectorManifest:
    def test_default(self):
        m = ConnectorManifest()
        assert "foundation" in m.subsystems
        assert len(m.subsystems) == 11

    def test_immutable(self):
        m = ConnectorManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "2.0"


# ============================================================
# Bridges
# ============================================================
class TestConversationCertificationBridge:
    def test_certify(self):
        b = ConversationCertificationBridge(_ready_registry())
        assert b.certify().certified is True

    def test_score(self):
        b = ConversationCertificationBridge(_ready_registry())
        assert b.score("c1").score > 0

    def test_report(self):
        b = ConversationCertificationBridge(_ready_registry())
        assert b.report().certified is True


class TestDashboardCertificationBridge:
    def test_five_cards(self):
        b = DashboardCertificationBridge(_ready_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict_certified(self):
        b = DashboardCertificationBridge(_ready_registry())
        assert "certified" in b.verdict_card().summary.lower()


# ============================================================
# Immutability
# ============================================================
class TestCertificationImmutability:
    DTO_CLASSES = [
        CertificationCriterion, CertificationResult, ConnectorScore,
        CertificationValidation, ConnectorReport, ConnectorManifest,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
