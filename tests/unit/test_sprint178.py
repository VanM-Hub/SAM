"""Sprint 178 — Memory Certification Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.memory.certification.memory_certification import (
    MemoryCertification, MemoryCertificationCriterion, MemoryCertificationResult,
)
from sam.memory.certification.memory_score import (
    MemoryScore, MemoryScoreDimension, MemoryScorer,
)
from sam.memory.certification.memory_manifest import MemoryManifest
from sam.memory.certification.memory_report import (
    MemoryCertificationReport, MemoryCertificationReporter,
)
from sam.memory.certification.memory_certification_validator import (
    MemoryCertificationValidation, MemoryCertificationValidator,
)
from sam.memory.certification.conversation_certification import (
    ConversationCertificationBridge,
)
from sam.memory.certification.dashboard_certification import (
    DashboardCertificationBridge,
)
from sam.memory.dashboard.memory_dashboard import ExecutionCard


class TestMemoryCertification:
    DIMENSIONS = [
        "Structure", "Integrity", "Consistency", "Completeness",
        "Determinism", "Immutability", "PreviewOnly",
    ]

    def test_dimensions(self):
        assert MemoryCertification.DIMENSIONS == self.DIMENSIONS

    def test_certified(self):
        c = MemoryCertification()
        res = c.certify(modules_present=9, modules_expected=9, dto_frozen=True,
                        no_forbidden_imports=True, no_write=True,
                        deterministic=True, preview_only=True)
        assert res.certified is True
        assert res.score == 100.0
        assert len(res.criteria) == 7

    def test_not_certified_incomplete(self):
        c = MemoryCertification()
        res = c.certify(modules_present=5, modules_expected=9)
        assert res.certified is False

    def test_not_certified_write(self):
        c = MemoryCertification()
        res = c.certify(modules_present=9, modules_expected=9, no_write=False)
        assert res.certified is False

    def test_not_certified_preview(self):
        c = MemoryCertification()
        res = c.certify(modules_present=9, modules_expected=9, preview_only=False)
        assert res.certified is False


class TestMemoryCertificationCriterion:
    def test_default(self):
        assert MemoryCertificationCriterion("x").passed is False

    def test_immutable(self):
        c = MemoryCertificationCriterion("x")
        with pytest.raises(FrozenInstanceError):
            c.passed = True


class TestMemoryCertificationResult:
    def test_default(self):
        assert MemoryCertificationResult().certified is False

    def test_immutable(self):
        r = MemoryCertificationResult()
        with pytest.raises(FrozenInstanceError):
            r.certified = True


class TestMemoryScorer:
    def test_full(self):
        criteria = [
            MemoryCertificationCriterion("a", True),
            MemoryCertificationCriterion("b", True),
        ]
        assert MemoryScorer().compute(criteria) == 100.0

    def test_half(self):
        criteria = [
            MemoryCertificationCriterion("a", True),
            MemoryCertificationCriterion("b", False),
        ]
        assert MemoryScorer().compute(criteria) == 50.0

    def test_empty(self):
        assert MemoryScorer().compute([]) == 0.0

    def test_dimension_scores(self):
        criteria = [
            MemoryCertificationCriterion("a", True),
            MemoryCertificationCriterion("b", False),
        ]
        dims = MemoryScorer().dimension_scores(criteria)
        assert dims[0].score == 50.0
        assert dims[1].score == 0.0


class TestMemoryScore:
    def test_default(self):
        assert MemoryScore().total == 0.0

    def test_immutable(self):
        s = MemoryScore()
        with pytest.raises(FrozenInstanceError):
            s.total = 1.0


class TestMemoryScoreDimension:
    def test_default(self):
        assert MemoryScoreDimension("x").max_score == 100.0


class TestMemoryManifest:
    def test_subsystems(self):
        m = MemoryManifest()
        assert len(m.subsystems) == 9
        assert "foundation" in m.subsystems

    def test_version(self):
        assert MemoryManifest().version == "17.0.0"

    def test_preview(self):
        assert MemoryManifest().preview_only is True

    def test_immutable(self):
        m = MemoryManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestMemoryCertificationReporter:
    def test_certified(self):
        c = MemoryCertification()
        res = c.certify(modules_present=9, modules_expected=9)
        rep = MemoryCertificationReporter().report(res)
        assert rep.certified is True
        assert "CERTIFIED" in rep.headline


class TestMemoryCertificationReport:
    def test_immutable(self):
        rep = MemoryCertificationReport()
        with pytest.raises(FrozenInstanceError):
            rep.certified = True


class TestMemoryCertificationValidator:
    def test_valid(self):
        v = MemoryCertificationValidator().validate()
        assert v.valid is True
        assert v.issues == []

    def test_invalid_write(self):
        v = MemoryCertificationValidator().validate(no_write=False)
        assert v.valid is False
        assert "write detected (filesystem/database)" in v.issues

    def test_invalid_frozen(self):
        v = MemoryCertificationValidator().validate(frozen=False)
        assert v.valid is False


class TestMemoryCertificationValidation:
    def test_default(self):
        assert MemoryCertificationValidation().valid is True


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
        MemoryCertificationCriterion, MemoryCertificationResult,
        MemoryScore, MemoryScoreDimension, MemoryManifest,
        MemoryCertificationReport, MemoryCertificationValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
