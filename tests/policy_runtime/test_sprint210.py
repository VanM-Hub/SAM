"""Sprint 210 — Policy Certification Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.policy_runtime.certification.policy_certification import (
    PolicyCertification, PolicyCertificationCriterion,
    PolicyCertificationResult,
)
from sam.policy_runtime.certification.policy_score import (
    PolicyScore, PolicyScoreDimension, PolicyScorer,
)
from sam.policy_runtime.certification.policy_manifest import PolicyManifest
from sam.policy_runtime.certification.policy_report import (
    PolicyCertificationReport, PolicyCertificationReporter,
)
from sam.policy_runtime.certification.policy_certification_validator import (
    PolicyCertificationValidation, PolicyCertificationValidator,
)
from sam.policy_runtime.certification.conversation_certification import (
    ConversationCertificationBridge,
)
from sam.policy_runtime.certification.dashboard_certification import (
    DashboardCertificationBridge,
)
from sam.policy_runtime.dashboard import PolicyCard


class TestPolicyCertification:
    DIMENSIONS = [
        "Structure", "Integrity", "Consistency", "Completeness",
        "Determinism", "Immutability", "PreviewOnly",
    ]

    def test_dimensions(self):
        assert PolicyCertification.DIMENSIONS == self.DIMENSIONS

    def test_certified(self):
        c = PolicyCertification()
        res = c.certify(modules_present=9, modules_expected=9, dto_frozen=True,
                        no_forbidden_imports=True, no_inference=True, no_write=True,
                        deterministic=True, preview_only=True)
        assert res.certified is True
        assert res.score == 100.0
        assert len(res.criteria) == 7

    def test_not_certified_incomplete(self):
        c = PolicyCertification()
        res = c.certify(modules_present=5, modules_expected=9)
        assert res.certified is False

    def test_not_certified_inference(self):
        c = PolicyCertification()
        res = c.certify(modules_present=9, modules_expected=9, no_inference=False)
        assert res.certified is False

    def test_not_certified_write(self):
        c = PolicyCertification()
        res = c.certify(modules_present=9, modules_expected=9, no_write=False)
        assert res.certified is False


class TestPolicyCertificationCriterion:
    def test_default(self):
        assert PolicyCertificationCriterion("x").passed is False

    def test_immutable(self):
        c = PolicyCertificationCriterion("x")
        with pytest.raises(FrozenInstanceError):
            c.passed = True


class TestPolicyCertificationResult:
    def test_default(self):
        assert PolicyCertificationResult().certified is False

    def test_immutable(self):
        r = PolicyCertificationResult()
        with pytest.raises(FrozenInstanceError):
            r.certified = True


class TestPolicyScorer:
    def test_full(self):
        criteria = [
            PolicyCertificationCriterion("a", True),
            PolicyCertificationCriterion("b", True),
        ]
        assert PolicyScorer().compute(criteria) == 100.0

    def test_half(self):
        criteria = [
            PolicyCertificationCriterion("a", True),
            PolicyCertificationCriterion("b", False),
        ]
        assert PolicyScorer().compute(criteria) == 50.0

    def test_empty(self):
        assert PolicyScorer().compute([]) == 0.0

    def test_dimension_scores(self):
        criteria = [
            PolicyCertificationCriterion("a", True),
            PolicyCertificationCriterion("b", False),
        ]
        dims = PolicyScorer().dimension_scores(criteria)
        assert dims[0].score == 50.0
        assert dims[1].score == 0.0


class TestPolicyScore:
    def test_default(self):
        assert PolicyScore().total == 0.0

    def test_immutable(self):
        s = PolicyScore()
        with pytest.raises(FrozenInstanceError):
            s.total = 1.0


class TestPolicyScoreDimension:
    def test_default(self):
        assert PolicyScoreDimension("x").max_score == 100.0


class TestPolicyManifest:
    def test_subsystems(self):
        m = PolicyManifest()
        assert len(m.subsystems) == 9
        assert "foundation" in m.subsystems
        assert "monitoring" in m.subsystems

    def test_version(self):
        assert PolicyManifest().version == "21.0.0"

    def test_no_inference(self):
        assert PolicyManifest().no_inference is True

    def test_immutable(self):
        m = PolicyManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestPolicyCertificationReporter:
    def test_certified(self):
        c = PolicyCertification()
        res = c.certify(modules_present=9, modules_expected=9)
        rep = PolicyCertificationReporter().report(res)
        assert rep.certified is True
        assert "CERTIFIED" in rep.headline


class TestPolicyCertificationReport:
    def test_immutable(self):
        rep = PolicyCertificationReport()
        with pytest.raises(FrozenInstanceError):
            rep.certified = True


class TestPolicyCertificationValidator:
    def test_valid(self):
        v = PolicyCertificationValidator().validate()
        assert v.valid is True
        assert v.issues == []

    def test_invalid_write(self):
        v = PolicyCertificationValidator().validate(no_write=False)
        assert v.valid is False
        assert "write detected (filesystem/database)" in v.issues

    def test_invalid_inference(self):
        v = PolicyCertificationValidator().validate(no_inference=False)
        assert v.valid is False
        assert "inference detected" in v.issues

    def test_invalid_frozen(self):
        v = PolicyCertificationValidator().validate(frozen=False)
        assert v.valid is False


class TestPolicyCertificationValidation:
    def test_default(self):
        assert PolicyCertificationValidation().valid is True


class TestConversationCertificationBridge:
    def test_summary(self):
        b = ConversationCertificationBridge()
        s = b.summary()
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
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_verdict(self):
        b = DashboardCertificationBridge()
        assert b.verdict_card().verdict == "certified"


class TestCertificationImmutability:
    DTO_CLASSES = [
        PolicyCertificationCriterion, PolicyCertificationResult,
        PolicyScore, PolicyScoreDimension, PolicyManifest,
        PolicyCertificationReport, PolicyCertificationValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
