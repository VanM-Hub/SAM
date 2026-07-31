"""Sprint 194 — Cognitive Certification Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.cognitive_runtime.certification.cognitive_certification import (
    CognitiveCertification, CognitiveCertificationCriterion,
    CognitiveCertificationResult,
)
from sam.cognitive_runtime.certification.cognitive_score import (
    CognitiveScore, CognitiveScoreDimension, CognitiveScorer,
)
from sam.cognitive_runtime.certification.cognitive_manifest import CognitiveManifest
from sam.cognitive_runtime.certification.cognitive_report import (
    CognitiveCertificationReport, CognitiveCertificationReporter,
)
from sam.cognitive_runtime.certification.cognitive_certification_validator import (
    CognitiveCertificationValidation, CognitiveCertificationValidator,
)
from sam.cognitive_runtime.certification.conversation_certification import (
    ConversationCertificationBridge,
)
from sam.cognitive_runtime.certification.dashboard_certification import (
    DashboardCertificationBridge,
)
from sam.cognitive_runtime.dashboard import ExecutionCard


class TestCognitiveCertification:
    DIMENSIONS = [
        "Structure", "Integrity", "Consistency", "Completeness",
        "Determinism", "Immutability", "PreviewOnly",
    ]

    def test_dimensions(self):
        assert CognitiveCertification.DIMENSIONS == self.DIMENSIONS

    def test_certified(self):
        c = CognitiveCertification()
        res = c.certify(modules_present=9, modules_expected=9, dto_frozen=True,
                        no_forbidden_imports=True, no_inference=True, no_write=True,
                        deterministic=True, preview_only=True)
        assert res.certified is True
        assert res.score == 100.0
        assert len(res.criteria) == 7

    def test_not_certified_incomplete(self):
        c = CognitiveCertification()
        res = c.certify(modules_present=5, modules_expected=9)
        assert res.certified is False

    def test_not_certified_inference(self):
        c = CognitiveCertification()
        res = c.certify(modules_present=9, modules_expected=9, no_inference=False)
        assert res.certified is False

    def test_not_certified_write(self):
        c = CognitiveCertification()
        res = c.certify(modules_present=9, modules_expected=9, no_write=False)
        assert res.certified is False


class TestCognitiveCertificationCriterion:
    def test_default(self):
        assert CognitiveCertificationCriterion("x").passed is False

    def test_immutable(self):
        c = CognitiveCertificationCriterion("x")
        with pytest.raises(FrozenInstanceError):
            c.passed = True


class TestCognitiveCertificationResult:
    def test_default(self):
        assert CognitiveCertificationResult().certified is False

    def test_immutable(self):
        r = CognitiveCertificationResult()
        with pytest.raises(FrozenInstanceError):
            r.certified = True


class TestCognitiveScorer:
    def test_full(self):
        criteria = [
            CognitiveCertificationCriterion("a", True),
            CognitiveCertificationCriterion("b", True),
        ]
        assert CognitiveScorer().compute(criteria) == 100.0

    def test_half(self):
        criteria = [
            CognitiveCertificationCriterion("a", True),
            CognitiveCertificationCriterion("b", False),
        ]
        assert CognitiveScorer().compute(criteria) == 50.0

    def test_empty(self):
        assert CognitiveScorer().compute([]) == 0.0

    def test_dimension_scores(self):
        criteria = [
            CognitiveCertificationCriterion("a", True),
            CognitiveCertificationCriterion("b", False),
        ]
        dims = CognitiveScorer().dimension_scores(criteria)
        assert dims[0].score == 50.0
        assert dims[1].score == 0.0


class TestCognitiveScore:
    def test_default(self):
        assert CognitiveScore().total == 0.0

    def test_immutable(self):
        s = CognitiveScore()
        with pytest.raises(FrozenInstanceError):
            s.total = 1.0


class TestCognitiveScoreDimension:
    def test_default(self):
        assert CognitiveScoreDimension("x").max_score == 100.0


class TestCognitiveManifest:
    def test_subsystems(self):
        m = CognitiveManifest()
        assert len(m.subsystems) == 9
        assert "foundation" in m.subsystems
        assert "workspace" in m.subsystems

    def test_version(self):
        assert CognitiveManifest().version == "19.0.0"

    def test_no_inference(self):
        assert CognitiveManifest().no_inference is True

    def test_immutable(self):
        m = CognitiveManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestCognitiveCertificationReporter:
    def test_certified(self):
        c = CognitiveCertification()
        res = c.certify(modules_present=9, modules_expected=9)
        rep = CognitiveCertificationReporter().report(res)
        assert rep.certified is True
        assert "CERTIFIED" in rep.headline


class TestCognitiveCertificationReport:
    def test_immutable(self):
        rep = CognitiveCertificationReport()
        with pytest.raises(FrozenInstanceError):
            rep.certified = True


class TestCognitiveCertificationValidator:
    def test_valid(self):
        v = CognitiveCertificationValidator().validate()
        assert v.valid is True
        assert v.issues == []

    def test_invalid_write(self):
        v = CognitiveCertificationValidator().validate(no_write=False)
        assert v.valid is False
        assert "write detected (filesystem/database)" in v.issues

    def test_invalid_inference(self):
        v = CognitiveCertificationValidator().validate(no_inference=False)
        assert v.valid is False
        assert "inference detected" in v.issues

    def test_invalid_frozen(self):
        v = CognitiveCertificationValidator().validate(frozen=False)
        assert v.valid is False


class TestCognitiveCertificationValidation:
    def test_default(self):
        assert CognitiveCertificationValidation().valid is True


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
        CognitiveCertificationCriterion, CognitiveCertificationResult,
        CognitiveScore, CognitiveScoreDimension, CognitiveManifest,
        CognitiveCertificationReport, CognitiveCertificationValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
