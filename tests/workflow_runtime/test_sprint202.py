"""Sprint 202 — Workflow Certification Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.workflow_runtime.certification.workflow_certification import (
    WorkflowCertification, WorkflowCertificationCriterion,
    WorkflowCertificationResult,
)
from sam.workflow_runtime.certification.workflow_score import (
    WorkflowScore, WorkflowScoreDimension, WorkflowScorer,
)
from sam.workflow_runtime.certification.workflow_manifest import WorkflowManifest
from sam.workflow_runtime.certification.workflow_report import (
    WorkflowCertificationReport, WorkflowCertificationReporter,
)
from sam.workflow_runtime.certification.workflow_certification_validator import (
    WorkflowCertificationValidation, WorkflowCertificationValidator,
)
from sam.workflow_runtime.certification.conversation_certification import (
    ConversationCertificationBridge,
)
from sam.workflow_runtime.certification.dashboard_certification import (
    DashboardCertificationBridge,
)
from sam.workflow_runtime.dashboard import WorkflowCard


class TestWorkflowCertification:
    DIMENSIONS = [
        "Structure", "Integrity", "Consistency", "Completeness",
        "Determinism", "Immutability", "PreviewOnly",
    ]

    def test_dimensions(self):
        assert WorkflowCertification.DIMENSIONS == self.DIMENSIONS

    def test_certified(self):
        c = WorkflowCertification()
        res = c.certify(modules_present=9, modules_expected=9, dto_frozen=True,
                        no_forbidden_imports=True, no_inference=True, no_write=True,
                        deterministic=True, preview_only=True)
        assert res.certified is True
        assert res.score == 100.0
        assert len(res.criteria) == 7

    def test_not_certified_incomplete(self):
        c = WorkflowCertification()
        res = c.certify(modules_present=5, modules_expected=9)
        assert res.certified is False

    def test_not_certified_inference(self):
        c = WorkflowCertification()
        res = c.certify(modules_present=9, modules_expected=9, no_inference=False)
        assert res.certified is False

    def test_not_certified_write(self):
        c = WorkflowCertification()
        res = c.certify(modules_present=9, modules_expected=9, no_write=False)
        assert res.certified is False


class TestWorkflowCertificationCriterion:
    def test_default(self):
        assert WorkflowCertificationCriterion("x").passed is False

    def test_immutable(self):
        c = WorkflowCertificationCriterion("x")
        with pytest.raises(FrozenInstanceError):
            c.passed = True


class TestWorkflowCertificationResult:
    def test_default(self):
        assert WorkflowCertificationResult().certified is False

    def test_immutable(self):
        r = WorkflowCertificationResult()
        with pytest.raises(FrozenInstanceError):
            r.certified = True


class TestWorkflowScorer:
    def test_full(self):
        criteria = [
            WorkflowCertificationCriterion("a", True),
            WorkflowCertificationCriterion("b", True),
        ]
        assert WorkflowScorer().compute(criteria) == 100.0

    def test_half(self):
        criteria = [
            WorkflowCertificationCriterion("a", True),
            WorkflowCertificationCriterion("b", False),
        ]
        assert WorkflowScorer().compute(criteria) == 50.0

    def test_empty(self):
        assert WorkflowScorer().compute([]) == 0.0

    def test_dimension_scores(self):
        criteria = [
            WorkflowCertificationCriterion("a", True),
            WorkflowCertificationCriterion("b", False),
        ]
        dims = WorkflowScorer().dimension_scores(criteria)
        assert dims[0].score == 50.0
        assert dims[1].score == 0.0


class TestWorkflowScore:
    def test_default(self):
        assert WorkflowScore().total == 0.0

    def test_immutable(self):
        s = WorkflowScore()
        with pytest.raises(FrozenInstanceError):
            s.total = 1.0


class TestWorkflowScoreDimension:
    def test_default(self):
        assert WorkflowScoreDimension("x").max_score == 100.0


class TestWorkflowManifest:
    def test_subsystems(self):
        m = WorkflowManifest()
        assert len(m.subsystems) == 9
        assert "foundation" in m.subsystems
        assert "monitoring" in m.subsystems

    def test_version(self):
        assert WorkflowManifest().version == "20.0.0"

    def test_no_inference(self):
        assert WorkflowManifest().no_inference is True

    def test_immutable(self):
        m = WorkflowManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestWorkflowCertificationReporter:
    def test_certified(self):
        c = WorkflowCertification()
        res = c.certify(modules_present=9, modules_expected=9)
        rep = WorkflowCertificationReporter().report(res)
        assert rep.certified is True
        assert "CERTIFIED" in rep.headline


class TestWorkflowCertificationReport:
    def test_immutable(self):
        rep = WorkflowCertificationReport()
        with pytest.raises(FrozenInstanceError):
            rep.certified = True


class TestWorkflowCertificationValidator:
    def test_valid(self):
        v = WorkflowCertificationValidator().validate()
        assert v.valid is True
        assert v.issues == []

    def test_invalid_write(self):
        v = WorkflowCertificationValidator().validate(no_write=False)
        assert v.valid is False
        assert "write detected (filesystem/database)" in v.issues

    def test_invalid_inference(self):
        v = WorkflowCertificationValidator().validate(no_inference=False)
        assert v.valid is False
        assert "inference detected" in v.issues

    def test_invalid_frozen(self):
        v = WorkflowCertificationValidator().validate(frozen=False)
        assert v.valid is False


class TestWorkflowCertificationValidation:
    def test_default(self):
        assert WorkflowCertificationValidation().valid is True


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
        assert all(isinstance(c, WorkflowCard) for c in cards)

    def test_verdict(self):
        b = DashboardCertificationBridge()
        assert b.verdict_card().verdict == "certified"


class TestCertificationImmutability:
    DTO_CLASSES = [
        WorkflowCertificationCriterion, WorkflowCertificationResult,
        WorkflowScore, WorkflowScoreDimension, WorkflowManifest,
        WorkflowCertificationReport, WorkflowCertificationValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
