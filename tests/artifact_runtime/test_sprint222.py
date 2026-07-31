"""Sprint 222 — Artifact Builder Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.artifact_runtime.builder.artifact_builder import (
    ArtifactBuilder, ArtifactBuildResult, ArtifactPreviewDTO,
)
from sam.artifact_runtime.builder.manifest_builder import ManifestBuilder
from sam.artifact_runtime.builder.reference_builder import ReferenceBuilder
from sam.artifact_runtime.builder.metadata_builder import MetadataBuilder
from sam.artifact_runtime.builder.preview_builder import PreviewBuilder
from sam.artifact_runtime.builder.conversation_builder import (
    ConversationBuilderBridge,
)
from sam.artifact_runtime.builder.dashboard_builder import DashboardBuilderBridge
from sam.artifact_runtime.dashboard import PolicyCard


class TestArtifactBuilder:
    def _b(self):
        return ArtifactBuilder()

    def test_build_ok(self):
        res = self._b().build("out", "report")
        assert res.ok is True
        assert res.artifact.name == "out"
        assert res.artifact.no_storage is True

    def test_build_empty_name(self):
        res = self._b().build("")
        assert res.ok is False
        assert "name required" in res.error

    def test_no_write(self):
        # builder hanya menyusun DTO; tidak ada akses file
        a = self._b().build("x", "y").artifact
        assert a.no_storage is True


class TestArtifactBuildResult:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactBuildResult().ok = True


class TestArtifactPreviewDTO:
    def test_defaults(self):
        dto = ArtifactPreviewDTO()
        assert dto.stored is False
        assert dto.published is False
        assert dto.external_calls == 0

    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactPreviewDTO().stored = True


class TestManifestBuilder:
    def test_build(self):
        m = ManifestBuilder().build("mf", ("a", "b"))
        assert m.name == "mf"
        assert list(m.artifacts) == ["a", "b"]
        assert m.no_storage is True


class TestReferenceBuilder:
    def test_build(self):
        r = ReferenceBuilder().build("ref1")
        assert r.traceable is True


class TestMetadataBuilder:
    def test_build(self):
        m = MetadataBuilder().build("m1")
        assert m.version == "23.0.0"


class TestPreviewBuilder:
    def test_preview(self):
        dto = PreviewBuilder().preview("out", "report")
        assert dto.stored is False
        assert dto.published is False
        assert dto.external_calls == 0

    def test_cannot_publish(self):
        # membalik published harus ditolak (frozen + guard)
        with pytest.raises(FrozenInstanceError):
            PreviewBuilder().preview("x").published = True


class TestConversationBuilderBridge:
    def test_five_queries(self):
        b = ConversationBuilderBridge()
        assert b.query_1_build("ok")["ok"] is True
        assert b.query_2_manifest()["name"] == "mf"
        assert b.query_3_reference()["traceable"] is True
        assert b.query_4_metadata()["version"] == "23.0.0"
        assert b.query_5_preview("pre") is not None


class TestDashboardBuilderBridge:
    def test_five_cards(self):
        cards = DashboardBuilderBridge().cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)


class TestBuilderImmutability:
    DTO = [ArtifactBuildResult, ArtifactPreviewDTO]

    def test_all_frozen(self):
        for cls in self.DTO:
            assert cls.__dataclass_params__.frozen
