"""Sprint 226 — Artifact Certification Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.artifact_runtime.certification.artifact_certification import (
    ArtifactCertification, ArtifactCertificationCriterion,
    ArtifactCertificationResult,
)
from sam.artifact_runtime.certification.artifact_score import (
    ArtifactScore, ArtifactScorer, ArtifactCertificationDimension,
)
from sam.artifact_runtime.certification.artifact_manifest_report import (
    ArtifactManifestReport, ArtifactManifestReporter,
)
from sam.artifact_runtime.certification.artifact_certification_report import (
    ArtifactCertificationReport, ArtifactCertificationReporter,
)
from sam.artifact_runtime.certification.artifact_certification_validator import (
    ArtifactCertificationValidator, ArtifactCertificationValidation,
)
from sam.artifact_runtime.certification.conversation_certification import (
    ConversationCertificationBridge,
)
from sam.artifact_runtime.certification.dashboard_certification import (
    DashboardCertificationBridge,
)
from sam.artifact_runtime.dashboard import PolicyCard


class TestArtifactCertification:
    def test_all_passed(self):
        res = ArtifactCertification().certify()
        assert res.certified is True
        assert res.score == 100.0
        assert len(res.checks) == 7

    def test_dimensions_names(self):
        res = ArtifactCertification().certify()
        names = [c.name for c in res.checks]
        assert names == ["Structure", "Integrity", "Consistency",
                         "Completeness", "Determinism", "Immutability",
                         "PreviewOnly"]

    def test_structure_fail(self):
        res = ArtifactCertification(structure=False).certify()
        assert res.certified is False
        assert res.score < 100.0

    def test_no_storage_fail(self):
        res = ArtifactCertification(no_storage=False).certify()
        assert res.certified is False

    def test_preview_fail(self):
        res = ArtifactCertification(preview_only=False).certify()
        assert res.certified is False

    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactCertification().structure = False


class TestArtifactCertificationCriterion:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactCertificationCriterion().passed = False


class TestArtifactCertificationResult:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactCertificationResult().certified = False


class TestArtifactScorer:
    def test_score(self):
        res = ArtifactCertification().certify()
        s = ArtifactScorer().score(res)
        assert s.score == 100.0
        assert s.certified is True


class TestArtifactScore:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactScore().score = 0


class TestArtifactCertificationDimension:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactCertificationDimension().score = 0


class TestArtifactManifestReporter:
    def test_report(self):
        m = ArtifactManifestReporter().report(("mission", "agent", "artifact"))
        assert m.integrated == 3
        assert len(m.subsystems) == 3


class TestArtifactManifestReport:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactManifestReport().integrated = 5


class TestArtifactCertificationReporter:
    def test_report(self):
        r = ArtifactCertificationReporter().report(True, 100.0)
        assert r.certified is True
        assert r.score == 100.0


class TestArtifactCertificationReport:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactCertificationReport().score = 0


class TestArtifactCertificationValidator:
    def test_valid(self):
        res = ArtifactCertification().certify()
        assert ArtifactCertificationValidator().validate(res).valid is True

    def test_invalid_external_calls(self):
        class FakeResult:
            certified = True

            @property
            def external_calls(self):
                return 1

        v = ArtifactCertificationValidator().validate(FakeResult())
        assert v.valid is False


class TestArtifactCertificationValidation:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactCertificationValidation().valid = False


class TestConversationCertificationBridge:
    def test_five_queries(self):
        b = ConversationCertificationBridge()
        assert b.query_1_certify()["certified"] is True
        assert b.query_2_score()["score"] == 100.0
        assert b.query_3_manifest()["integrated"] == 3
        assert b.query_4_report()["external_calls"] == 0
        assert b.query_5_validate()["valid"] is True


class TestDashboardCertificationBridge:
    def test_five_cards(self):
        cards = DashboardCertificationBridge().cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_verdict(self):
        assert DashboardCertificationBridge().cards()[0].verdict == "certified"


class TestCertificationImmutability:
    DTO = [ArtifactCertification, ArtifactCertificationCriterion,
           ArtifactCertificationResult, ArtifactScore,
           ArtifactCertificationDimension, ArtifactManifestReport,
           ArtifactCertificationReport, ArtifactCertificationValidation]

    def test_all_frozen(self):
        for cls in self.DTO:
            assert cls.__dataclass_params__.frozen
