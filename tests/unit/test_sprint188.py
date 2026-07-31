"""Sprint 188 — Cognitive Foundation Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.cognitive_runtime.foundation.cognitive_descriptor import CognitiveDescriptor
from sam.cognitive_runtime.foundation.cognitive_capability import CognitiveCapability
from sam.cognitive_runtime.foundation.cognitive_contract import CognitiveContract
from sam.cognitive_runtime.foundation.cognitive_metadata import CognitiveMetadata
from sam.cognitive_runtime.foundation.cognitive_registry import CognitiveRegistry
from sam.cognitive_runtime.foundation.conversation_cognitive import ConversationCognitiveBridge
from sam.cognitive_runtime.foundation.dashboard_cognitive import DashboardCognitiveBridge
from sam.cognitive_runtime.dashboard import ExecutionCard


def _registry():
    r = CognitiveRegistry()
    r.register(CognitiveDescriptor("cog1", "Cognitive Core", category="core"))
    r.attach_capability(CognitiveCapability("cap1", "cog1", operations=["context"]))
    r.register(CognitiveDescriptor("cog2", "Cognitive Insight", category="insight"))
    return r


class TestCognitiveDescriptor:
    def test_basic(self):
        d = CognitiveDescriptor("cog1", "Core")
        assert d.id == "cog1"
        assert d.category == "cognitive"

    def test_empty_id_raises(self):
        with pytest.raises(ValueError):
            CognitiveDescriptor("", "x")

    def test_tags_default(self):
        assert CognitiveDescriptor("a", "b").tags == []

    def test_immutable(self):
        d = CognitiveDescriptor("cog1", "Core")
        with pytest.raises(FrozenInstanceError):
            d.name = "x"


class TestCognitiveCapability:
    def test_supports(self):
        c = CognitiveCapability("cap1", "cog1", operations=["context", "scope"])
        assert c.supports("context") is True
        assert c.supports("other") is False

    def test_no_inference_default(self):
        assert CognitiveCapability("c").no_inference is True

    def test_deterministic_default(self):
        assert CognitiveCapability("c").deterministic is True

    def test_immutable(self):
        c = CognitiveCapability("c")
        with pytest.raises(FrozenInstanceError):
            c.id = "x"


class TestCognitiveContract:
    def test_default(self):
        c = CognitiveContract("c1")
        assert c.preview_only is True
        assert c.version == "19.0.0"

    def test_hash_deterministic(self):
        c = CognitiveContract("c1", "cog1", ["a", "b"])
        assert c.hash() == c.hash()

    def test_hash_different(self):
        a = CognitiveContract("c1", "cog1", ["x"])
        b = CognitiveContract("c1", "cog1", ["y"])
        assert a.hash() != b.hash()

    def test_immutable(self):
        c = CognitiveContract("c1")
        with pytest.raises(FrozenInstanceError):
            c.version = "1"


class TestCognitiveMetadata:
    def test_default_no_inference(self):
        assert CognitiveMetadata().no_inference is True

    def test_default_preview(self):
        assert CognitiveMetadata().preview_only is True

    def test_created_at_generated(self):
        assert CognitiveMetadata().created_at != ""

    def test_immutable(self):
        m = CognitiveMetadata()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestCognitiveRegistry:
    def test_register_get(self):
        r = CognitiveRegistry()
        r.register(CognitiveDescriptor("cog1", "Core"))
        assert r.get("cog1").name == "Core"

    def test_exists(self):
        r = _registry()
        assert r.exists("cog1") is True
        assert r.exists("nope") is False

    def test_count(self):
        assert _registry().count() == 2

    def test_all(self):
        assert len(_registry().all()) == 2

    def test_capabilities(self):
        r = _registry()
        caps = r.capabilities("cog1")
        assert len(caps) == 1
        assert caps[0].id == "cap1"

    def test_missing_get(self):
        assert _registry().get("nope") is None


class TestConversationCognitiveBridge:
    def test_summary(self):
        b = ConversationCognitiveBridge(_registry())
        assert b.summary()["total_Cognitive"] == 2
        assert b.summary()["preview_only"] is True

    def test_status(self):
        b = ConversationCognitiveBridge(_registry())
        assert b.status("cog1") == "registered"
        assert b.status("nope") == "missing"


class TestDashboardCognitiveBridge:
    def test_five_cards(self):
        b = DashboardCognitiveBridge(_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardCognitiveBridge(_registry())
        assert b.overview_card().verdict == "ready"


class TestFoundationImmutability:
    DTO_CLASSES = [
        CognitiveDescriptor, CognitiveCapability, CognitiveContract,
        CognitiveMetadata, ExecutionCard,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
