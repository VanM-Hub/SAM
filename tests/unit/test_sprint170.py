"""Sprint 170 — Certification Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.skills.certification.skill_certification import (
    SkillCertification, CertificationCriterion, SkillCertificationResult,
)
from sam.skills.certification.skill_score import SkillScore, SkillScoreDimension, SkillScorer
from sam.skills.certification.skill_manifest import SkillManifest
from sam.skills.certification.skill_report import (
    SkillCertificationReport, SkillCertificationReporter,
)
from sam.skills.certification.skill_validator import SkillValidator, SkillValidation
from sam.skills.certification.conversation_certification import (
    ConversationCertificationBridge,
)
from sam.skills.certification.dashboard_certification import (
    DashboardCertificationBridge,
)
from sam.skills.dashboard.skill_dashboard import ExecutionCard


class TestSkillCertification:
    DIMENSIONS = [
        "Structure", "Integrity", "Consistency", "Completeness",
        "Determinism", "Immutability", "PreviewOnly",
    ]

    def test_dimensions(self):
        assert SkillCertification.DIMENSIONS == self.DIMENSIONS

    def test_certified(self):
        c = SkillCertification()
        res = c.certify(modules_present=9, modules_expected=9, dto_frozen=True,
                        no_forbidden_imports=True, deterministic=True,
                        preview_only=True)
        assert res.certified is True
        assert res.score == 100.0
        assert len(res.criteria) == 7

    def test_not_certified_incomplete(self):
        c = SkillCertification()
        res = c.certify(modules_present=5, modules_expected=9)
        assert res.certified is False

    def test_not_certified_not_preview(self):
        c = SkillCertification()
        res = c.certify(modules_present=9, modules_expected=9, preview_only=False)
        assert res.certified is False


class TestCertificationCriterion:
    def test_default(self):
        assert CertificationCriterion("x").passed is False

    def test_immutable(self):
        c = CertificationCriterion("x")
        with pytest.raises(FrozenInstanceError):
            c.passed = True


class TestSkillCertificationResult:
    def test_default(self):
        assert SkillCertificationResult().certified is False

    def test_immutable(self):
        r = SkillCertificationResult()
        with pytest.raises(FrozenInstanceError):
            r.certified = True


class TestSkillScorer:
    def test_full(self):
        criteria = [CertificationCriterion("a", True), CertificationCriterion("b", True)]
        assert SkillScorer().compute(criteria) == 100.0

    def test_half(self):
        criteria = [CertificationCriterion("a", True), CertificationCriterion("b", False)]
        assert SkillScorer().compute(criteria) == 50.0

    def test_empty(self):
        assert SkillScorer().compute([]) == 0.0

    def test_dimension_scores(self):
        criteria = [CertificationCriterion("a", True), CertificationCriterion("b", False)]
        dims = SkillScorer().dimension_scores(criteria)
        assert dims[0].score == 50.0
        assert dims[1].score == 0.0


class TestSkillScore:
    def test_default(self):
        assert SkillScore().total == 0.0


class TestSkillScoreDimension:
    def test_default(self):
        assert SkillScoreDimension("x").max_score == 100.0


class TestSkillManifest:
    def test_subsystems(self):
        m = SkillManifest()
        assert len(m.subsystems) == 9
        assert "foundation" in m.subsystems

    def test_version(self):
        assert SkillManifest().version == "16.0.0"

    def test_preview(self):
        assert SkillManifest().preview_only is True

    def test_immutable(self):
        m = SkillManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestSkillCertificationReporter:
    def test_certified(self):
        c = SkillCertification()
        res = c.certify(modules_present=9, modules_expected=9)
        rep = SkillCertificationReporter().report(res)
        assert rep.certified is True
        assert "CERTIFIED" in rep.headline


class TestSkillCertificationReport:
    def test_immutable(self):
        rep = SkillCertificationReport()
        with pytest.raises(FrozenInstanceError):
            rep.certified = True


class TestSkillValidator:
    def test_valid(self):
        v = SkillValidator().validate()
        assert v.valid is True
        assert v.issues == []

    def test_invalid_execution(self):
        v = SkillValidator().validate(no_execution=False)
        assert v.valid is False

    def test_invalid_frozen(self):
        v = SkillValidator().validate(frozen=False)
        assert "DTO not frozen" in v.issues


class TestSkillValidation:
    def test_default(self):
        assert SkillValidation().valid is True


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
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        b = DashboardCertificationBridge()
        assert b.verdict_card().verdict == "certified"


class TestCertificationImmutability:
    DTO_CLASSES = [
        CertificationCriterion, SkillCertificationResult,
        SkillScore, SkillScoreDimension, SkillManifest,
        SkillCertificationReport, SkillValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
