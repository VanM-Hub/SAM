"""Sprint 221 — Artifact Model Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.artifact_runtime.model.artifact import Artifact
from sam.artifact_runtime.model.artifact_reference import ArtifactReference
from sam.artifact_runtime.model.artifact_manifest import ArtifactManifest
from sam.artifact_runtime.model.artifact_metadata_model import ArtifactMetadata
from sam.artifact_runtime.model.artifact_validator import (
    ArtifactValidator, ArtifactValidation,
)
from sam.artifact_runtime.model.conversation_model import ConversationModelBridge
from sam.artifact_runtime.model.dashboard_model import DashboardModelBridge
from sam.artifact_runtime.dashboard import PolicyCard


class TestArtifact:
    def test_defaults(self):
        a = Artifact("out", "report")
        assert a.name == "out"
        assert a.kind == "report"
        assert a.immutable is True
        assert a.no_storage is True
        assert a.no_publish is True

    def test_immutable(self):
        a = Artifact("x", "y")
        with pytest.raises(FrozenInstanceError):
            a.no_storage = False


class TestArtifactReference:
    def test_defaults(self):
        r = ArtifactReference("ref")
        assert r.traceable is True
        assert r.immutable is True

    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactReference("x").traceable = False


class TestArtifactManifest:
    def test_defaults(self):
        m = ArtifactManifest("mf", ("a", "b"))
        assert list(m.artifacts) == ["a", "b"]
        assert m.no_storage is True
        assert m.preview_only is True


class TestArtifactMetadata:
    def test_defaults(self):
        m = ArtifactMetadata("meta")
        assert m.version == "23.0.0"
        assert m.immutable is True


class TestArtifactValidator:
    def test_valid(self):
        v = ArtifactValidator()
        assert v.validate(Artifact("out", "report")).valid is True

    def test_none(self):
        v = ArtifactValidator()
        assert v.validate(None).valid is False

    def test_storage_violation(self):
        v = ArtifactValidator()
        assert v.validate(Artifact("x", "y", no_storage=False)).valid is False

    def test_errors(self):
        v = ArtifactValidator()
        res = v.validate(None)
        assert "artifact is None" in res.errors


class TestArtifactValidation:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactValidation().valid = False


class TestConversationModelBridge:
    def test_five_queries(self):
        b = ConversationModelBridge()
        assert b.query_1_sample().kind == "report"
        assert b.query_2_validate("ok")["valid"] is True
        assert "name" in b.query_3_tags()["required"]
        assert b.query_4_immutable() is True
        assert "report" in b.query_5_kinds()


class TestDashboardModelBridge:
    def test_five_cards(self):
        cards = DashboardModelBridge().cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)


class TestModelImmutability:
    DTO = [Artifact, ArtifactReference, ArtifactManifest, ArtifactMetadata,
           ArtifactValidation]

    def test_all_frozen(self):
        for cls in self.DTO:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} not frozen"
