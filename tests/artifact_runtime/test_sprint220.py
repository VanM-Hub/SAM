"""Sprint 220 — Artifact Foundation Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.artifact_runtime.foundation.artifact_descriptor import ArtifactDescriptor
from sam.artifact_runtime.foundation.artifact_capability import ArtifactCapability
from sam.artifact_runtime.foundation.artifact_contract import ArtifactContract
from sam.artifact_runtime.foundation.artifact_metadata import ArtifactMetadata
from sam.artifact_runtime.foundation.artifact_registry import ArtifactRegistry
from sam.artifact_runtime.foundation.conversation_artifact import (
    ConversationArtifactBridge,
)
from sam.artifact_runtime.foundation.dashboard_artifact import (
    DashboardArtifactBridge,
)
from sam.artifact_runtime.dashboard import PolicyCard


class TestArtifactDescriptor:
    def test_defaults(self):
        d = ArtifactDescriptor("policy")
        assert d.version == "23.0.0"
        assert d.provenance is True
        assert d.preview_only is True

    def test_immutable(self):
        d = ArtifactDescriptor("x")
        with pytest.raises(FrozenInstanceError):
            d.provenance = False


class TestArtifactCapability:
    def test_no_storage(self):
        assert ArtifactCapability().no_storage is True
        assert ArtifactCapability().no_publish is True
        assert ArtifactCapability().no_execute is True

    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactCapability().no_storage = False


class TestArtifactContract:
    def test_defaults(self):
        assert ArtifactContract().preview_only is True
        assert ArtifactContract().deterministic_hash == "sha256"

    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactContract().no_storage = False


class TestArtifactMetadata:
    def test_defaults(self):
        assert ArtifactMetadata().phase == "XXIII"
        assert ArtifactMetadata().version == "23.0.0"

    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactMetadata().no_storage = False


class TestArtifactRegistry:
    def test_empty(self):
        assert ArtifactRegistry().count() == 0

    def test_register_immutable(self):
        r0 = ArtifactRegistry()
        r1 = r0.register(ArtifactDescriptor("a"))
        r2 = r1.register(ArtifactDescriptor("b"))
        assert r0.count() == 0  # r0 tidak berubah
        assert r1.count() == 1
        assert r2.count() == 2

    def test_lookup(self):
        r = ArtifactRegistry().register(ArtifactDescriptor("plan"))
        assert r.lookup("plan").name == "plan"
        assert r.lookup("nope") is None

    def test_names(self):
        r = ArtifactRegistry().register(ArtifactDescriptor("a")).register(
            ArtifactDescriptor("b"))
        assert r.names() == ("a", "b")


class TestConversationArtifactBridge:
    def _reg(self):
        return ArtifactRegistry().register(ArtifactDescriptor("out"))

    def test_five_queries(self):
        b = ConversationArtifactBridge(self._reg())
        assert len(b.query_1_descriptors()) == 1
        assert b.query_2_count() == 1
        assert b.query_3_names() == ("out",)
        assert b.query_4_lookup("out").name == "out"
        assert b.query_5_metadata()["version"] == "23.0.0"


class TestDashboardArtifactBridge:
    def _reg(self):
        return ArtifactRegistry().register(ArtifactDescriptor("out"))

    def test_five_cards(self):
        cards = DashboardArtifactBridge(self._reg()).cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_verdict(self):
        assert DashboardArtifactBridge(self._reg()).cards()[0].verdict == "ready"
