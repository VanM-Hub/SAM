"""Sprint 218 — Audit Certification Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.audit_runtime.certification.audit_certification import (
    AuditCertification, AuditCertificationCriterion, AuditCertificationResult,
)
from sam.audit_runtime.certification.audit_score import (
    AuditScore, AuditScoreDimension, PolicyScorer,
)
from sam.audit_runtime.certification.audit_manifest import AuditManifest
from sam.audit_runtime.certification.audit_report import (
    AuditCertificationReport, AuditCertificationReporter,
)
from sam.audit_runtime.certification.audit_certification_validator import (
    AuditCertificationValidation, AuditCertificationValidator,
)
from sam.audit_runtime.certification.conversation_certification import (
    ConversationCertificationBridge,
)
from sam.audit_runtime.certification.dashboard_certification import (
    DashboardCertificationBridge,
)
from sam.audit_runtime.dashboard import PolicyCard


class TestAuditCertification:
    DIMENSIONS = ["Structure", "Integrity", "Consistency", "Completeness",
                  "Determinism", "Immutability", "PreviewOnly"]

    def test_dimensions(self):
        assert list(AuditCertification.DIMENSIONS) == self.DIMENSIONS

    def test_certified(self):
        c = AuditCertification().certify()
        assert c.certified is True
        assert c.score == 100.0
        assert len(c.criteria) == 7

    def test_not_certified_incomplete(self):
        assert AuditCertification().certify(modules_present=5).certified is False

    def test_not_certified_inference(self):
        assert AuditCertification().certify(no_inference=False).certified is False

    def test_not_certified_write(self):
        assert AuditCertification().certify(no_write=False).certified is False


class TestAuditCertificationCriterion:
    def test_default(self):
        assert AuditCertificationCriterion("x").passed is False

    def test_immutable(self):
        c = AuditCertificationCriterion("x")
        with pytest.raises(FrozenInstanceError):
            c.passed = True


class TestAuditCertificationResult:
    def test_immutable(self):
        r = AuditCertificationResult()
        with pytest.raises(FrozenInstanceError):
            r.certified = True


class TestPolicyScorer:
    def test_full(self):
        criteria = [AuditCertificationCriterion("a", True),
                    AuditCertificationCriterion("b", True)]
        assert PolicyScorer.compute(criteria) == 100.0

    def test_half(self):
        criteria = [AuditCertificationCriterion("a", True),
                    AuditCertificationCriterion("b", False)]
        assert PolicyScorer.compute(criteria) == 50.0

    def test_empty(self):
        assert PolicyScorer.compute([]) == 0.0

    def test_dimension_scores(self):
        criteria = [AuditCertificationCriterion("a", True),
                    AuditCertificationCriterion("b", False)]
        dims = PolicyScorer.dimension_scores(criteria)
        assert dims[0].score == 100.0
        assert dims[1].score == 0.0


class TestAuditScore:
    def test_immutable(self):
        s = AuditScore()
        with pytest.raises(FrozenInstanceError):
            s.total = 1.0


class TestAuditScoreDimension:
    def test_default(self):
        assert AuditScoreDimension("x").max_score == 100.0


class TestAuditManifest:
    def test_subsystems(self):
        m = AuditManifest()
        assert len(m.subsystems) == 9
        assert "foundation" in m.subsystems
        assert "monitoring" in m.subsystems

    def test_version(self):
        assert AuditManifest().version == "22.0.0"

    def test_no_inference(self):
        assert AuditManifest().no_inference is True

    def test_immutable(self):
        m = AuditManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestAuditCertificationReporter:
    def test_certified(self):
        r = AuditCertification().certify()
        rep = AuditCertificationReporter().report(r)
        assert rep.certified is True
        assert "CERTIFIED" in rep.headline


class TestAuditCertificationReport:
    def test_immutable(self):
        rep = AuditCertificationReport()
        with pytest.raises(FrozenInstanceError):
            rep.certified = True


class TestAuditCertificationValidator:
    def test_valid(self):
        v = AuditCertificationValidator().validate()
        assert v.valid is True
        assert v.issues == []

    def test_invalid_write(self):
        v = AuditCertificationValidator().validate(no_write=False)
        assert v.valid is False
        assert "write detected" in v.issues[0]

    def test_invalid_inference(self):
        v = AuditCertificationValidator().validate(no_inference=False)
        assert v.valid is False
        assert "inference detected" in v.issues[0]

    def test_invalid_execute(self):
        v = AuditCertificationValidator().validate(no_execute=False)
        assert v.valid is False

    def test_invalid_external_calls(self):
        v = AuditCertificationValidator().validate(external_calls=1)
        assert v.valid is False


class TestAuditCertificationValidation:
    def test_default(self):
        assert AuditCertificationValidation().valid is True


class TestConversationCertificationBridge:
    def test_5_queries(self):
        b = ConversationCertificationBridge()
        assert b.query_1_certify()["certified"] is True
        assert len(b.query_2_dimensions()["dimensions"]) == 7
        assert len(b.query_3_criteria()["passed"]) == 7
        assert b.query_4_validate()["valid"] is True
        assert b.query_5_preview()["no_execute"] is True


class TestDashboardCertificationBridge:
    def test_five_cards(self):
        b = DashboardCertificationBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_verdict(self):
        b = DashboardCertificationBridge()
        assert b.verdict_card().verdict == "certified"


class TestCertificationImmutability:
    DTO_CLASSES = [
        AuditCertificationCriterion, AuditCertificationResult, AuditScore,
        AuditScoreDimension, AuditManifest, AuditCertificationReport,
        AuditCertificationValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
