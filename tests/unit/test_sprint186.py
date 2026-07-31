"""Sprint 186 — Knowledge Certification Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.knowledge_runtime.certification.knowledge_certification import (
    KnowledgeCertification, KnowledgeCertificationCriterion,
    KnowledgeCertificationResult,
)
from sam.knowledge_runtime.certification.knowledge_score import (
    KnowledgeScore, KnowledgeScoreDimension, KnowledgeScorer,
)
from sam.knowledge_runtime.certification.knowledge_manifest import KnowledgeManifest
from sam.knowledge_runtime.certification.knowledge_report import (
    KnowledgeCertificationReport, KnowledgeCertificationReporter,
)
from sam.knowledge_runtime.certification.knowledge_certification_validator import (
    KnowledgeCertificationValidation, KnowledgeCertificationValidator,
)
from sam.knowledge_runtime.certification.conversation_certification import (
    ConversationCertificationBridge,
)
from sam.knowledge_runtime.certification.dashboard_certification import (
    DashboardCertificationBridge,
)
from sam.knowledge_runtime.dashboard.knowledge_dashboard import ExecutionCard


class TestKnowledgeCertification:
    DIMENSIONS = [
        "Structure", "Integrity", "Consistency", "Completeness",
        "Determinism", "Immutability", "PreviewOnly",
    ]

    def test_dimensions(self):
        assert KnowledgeCertification.DIMENSIONS == self.DIMENSIONS

    def test_certified(self):
        c = KnowledgeCertification()
        res = c.certify(modules_present=9, modules_expected=9, dto_frozen=True,
                        no_forbidden_imports=True, no_inference=True, no_write=True,
                        deterministic=True, preview_only=True)
        assert res.certified is True
        assert res.score == 100.0
        assert len(res.criteria) == 7

    def test_not_certified_incomplete(self):
        c = KnowledgeCertification()
        res = c.certify(modules_present=5, modules_expected=9)
        assert res.certified is False

    def test_not_certified_inference(self):
        c = KnowledgeCertification()
        res = c.certify(modules_present=9, modules_expected=9, no_inference=False)
        assert res.certified is False

    def test_not_certified_write(self):
        c = KnowledgeCertification()
        res = c.certify(modules_present=9, modules_expected=9, no_write=False)
        assert res.certified is False


class TestKnowledgeCertificationCriterion:
    def test_default(self):
        assert KnowledgeCertificationCriterion("x").passed is False

    def test_immutable(self):
        c = KnowledgeCertificationCriterion("x")
        with pytest.raises(FrozenInstanceError):
            c.passed = True


class TestKnowledgeCertificationResult:
    def test_default(self):
        assert KnowledgeCertificationResult().certified is False

    def test_immutable(self):
        r = KnowledgeCertificationResult()
        with pytest.raises(FrozenInstanceError):
            r.certified = True


class TestKnowledgeScorer:
    def test_full(self):
        criteria = [
            KnowledgeCertificationCriterion("a", True),
            KnowledgeCertificationCriterion("b", True),
        ]
        assert KnowledgeScorer().compute(criteria) == 100.0

    def test_half(self):
        criteria = [
            KnowledgeCertificationCriterion("a", True),
            KnowledgeCertificationCriterion("b", False),
        ]
        assert KnowledgeScorer().compute(criteria) == 50.0

    def test_empty(self):
        assert KnowledgeScorer().compute([]) == 0.0

    def test_dimension_scores(self):
        criteria = [
            KnowledgeCertificationCriterion("a", True),
            KnowledgeCertificationCriterion("b", False),
        ]
        dims = KnowledgeScorer().dimension_scores(criteria)
        assert dims[0].score == 50.0
        assert dims[1].score == 0.0


class TestKnowledgeScore:
    def test_default(self):
        assert KnowledgeScore().total == 0.0

    def test_immutable(self):
        s = KnowledgeScore()
        with pytest.raises(FrozenInstanceError):
            s.total = 1.0


class TestKnowledgeScoreDimension:
    def test_default(self):
        assert KnowledgeScoreDimension("x").max_score == 100.0


class TestKnowledgeManifest:
    def test_subsystems(self):
        m = KnowledgeManifest()
        assert len(m.subsystems) == 9
        assert "foundation" in m.subsystems

    def test_version(self):
        assert KnowledgeManifest().version == "18.0.0"

    def test_no_inference(self):
        assert KnowledgeManifest().no_inference is True

    def test_immutable(self):
        m = KnowledgeManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestKnowledgeCertificationReporter:
    def test_certified(self):
        c = KnowledgeCertification()
        res = c.certify(modules_present=9, modules_expected=9)
        rep = KnowledgeCertificationReporter().report(res)
        assert rep.certified is True
        assert "CERTIFIED" in rep.headline


class TestKnowledgeCertificationReport:
    def test_immutable(self):
        rep = KnowledgeCertificationReport()
        with pytest.raises(FrozenInstanceError):
            rep.certified = True


class TestKnowledgeCertificationValidator:
    def test_valid(self):
        v = KnowledgeCertificationValidator().validate()
        assert v.valid is True
        assert v.issues == []

    def test_invalid_write(self):
        v = KnowledgeCertificationValidator().validate(no_write=False)
        assert v.valid is False
        assert "write detected (filesystem/database)" in v.issues

    def test_invalid_inference(self):
        v = KnowledgeCertificationValidator().validate(no_inference=False)
        assert v.valid is False
        assert "inference detected" in v.issues

    def test_invalid_frozen(self):
        v = KnowledgeCertificationValidator().validate(frozen=False)
        assert v.valid is False


class TestKnowledgeCertificationValidation:
    def test_default(self):
        assert KnowledgeCertificationValidation().valid is True


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
        KnowledgeCertificationCriterion, KnowledgeCertificationResult,
        KnowledgeScore, KnowledgeScoreDimension, KnowledgeManifest,
        KnowledgeCertificationReport, KnowledgeCertificationValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
