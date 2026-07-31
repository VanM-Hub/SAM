"""Sprint 163 — Certification Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.agent.certification.agent_certification import (
    AgentCertification, CertificationCriterion, CertificationResult,
)
from sam.agent.certification.agent_score import AgentScore, AgentScorer, ScoreDimension
from sam.agent.certification.agent_validator import AgentValidator, AgentValidation
from sam.agent.certification.agent_manifest import AgentManifest
from sam.agent.certification.agent_report import AgentReport, AgentReporter
from sam.agent.certification.conversation_certification import ConversationCertificationBridge
from sam.agent.certification.dashboard_certification import DashboardCertificationBridge
from sam.agent.dashboard.agent_dashboard import ExecutionCard


class TestAgentCertification:
    DIMENSIONS = [
        "Completeness", "Consistency", "Determinism", "Layer Safety",
        "Architecture Safety", "DTO Safety", "Pipeline Safety",
    ]

    def test_dimensions(self):
        assert AgentCertification.DIMENSIONS == self.DIMENSIONS

    def test_certified(self):
        c = AgentCertification()
        res = c.certify(modules_present=10, modules_expected=10,
                        dto_frozen=True, no_forbidden_imports=True,
                        deterministic=True)
        assert res.certified is True
        assert res.total_score == 100.0
        assert len(res.criteria) == 7

    def test_not_certified_incomplete(self):
        c = AgentCertification()
        res = c.certify(modules_present=5, modules_expected=10)
        assert res.certified is False

    def test_not_certified_dto(self):
        c = AgentCertification()
        res = c.certify(modules_present=10, modules_expected=10, dto_frozen=False)
        assert res.certified is False


class TestCertificationCriterion:
    def test_default(self):
        assert CertificationCriterion("x").passed is False

    def test_immutable(self):
        c = CertificationCriterion("x")
        with pytest.raises(FrozenInstanceError):
            c.passed = True


class TestCertificationResult:
    def test_default(self):
        assert CertificationResult().certified is False

    def test_immutable(self):
        r = CertificationResult()
        with pytest.raises(FrozenInstanceError):
            r.certified = True


class TestAgentScorer:
    def test_full(self):
        criteria = [CertificationCriterion("a", True), CertificationCriterion("b", True)]
        assert AgentScorer().compute(criteria) == 100.0

    def test_half(self):
        criteria = [CertificationCriterion("a", True), CertificationCriterion("b", False)]
        assert AgentScorer().compute(criteria) == 50.0

    def test_empty(self):
        assert AgentScorer().compute([]) == 0.0

    def test_dimension_scores(self):
        criteria = [CertificationCriterion("a", True), CertificationCriterion("b", False)]
        dims = AgentScorer().dimension_scores(criteria)
        assert dims[0].score == 50.0
        assert dims[1].score == 0.0


class TestAgentScore:
    def test_default(self):
        assert AgentScore().total == 0.0

    def test_immutable(self):
        s = AgentScore()
        with pytest.raises(FrozenInstanceError):
            s.total = 1.0


class TestScoreDimension:
    def test_default(self):
        assert ScoreDimension("x").max_score == 100.0


class TestAgentValidator:
    def test_valid(self):
        v = AgentValidator().validate()
        assert v.valid is True
        assert v.issues == []

    def test_invalid_frozen(self):
        v = AgentValidator().validate(frozen=False)
        assert v.valid is False
        assert "DTO not frozen" in v.issues

    def test_invalid_execution(self):
        v = AgentValidator().validate(no_execution=False)
        assert v.valid is False


class TestAgentValidation:
    def test_default(self):
        assert AgentValidation().valid is True


class TestAgentManifest:
    def test_default_subsystems(self):
        m = AgentManifest()
        assert len(m.subsystems) == 10
        assert "foundation" in m.subsystems
        "dashboard" in m.subsystems

    def test_version(self):
        assert AgentManifest().version == "15.0.0"

    def test_preview(self):
        assert AgentManifest().preview_only is True

    def test_immutable(self):
        m = AgentManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestAgentReport:
    def test_report_certified(self):
        c = AgentCertification()
        res = c.certify(modules_present=10, modules_expected=10)
        rep = AgentReporter().report(res)
        assert rep.certified is True
        assert "CERTIFIED" in rep.headline

    def test_report_not_certified(self):
        res = AgentCertification().certify(modules_present=1, modules_expected=10)
        rep = AgentReporter().report(res)
        assert rep.certified is False

    def test_immutable(self):
        rep = AgentReport()
        with pytest.raises(FrozenInstanceError):
            rep.certified = True


class TestConversationCertificationBridge:
    def test_show_summary(self):
        b = ConversationCertificationBridge()
        s = b.show_summary()
        assert s["certified"] is True
        assert len(s["criteria"]) == 7

    def test_status(self):
        b = ConversationCertificationBridge()
        assert b.status() == "certified"


class TestDashboardCertificationBridge:
    def test_five_cards(self):
        b = DashboardCertificationBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        b = DashboardCertificationBridge()
        assert b.verdict_card().verdict == "certified"


class TestCertificationImmutability:
    DTO_CLASSES = [
        CertificationCriterion, CertificationResult,
        AgentScore, ScoreDimension, AgentValidation,
        AgentManifest, AgentReport,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
