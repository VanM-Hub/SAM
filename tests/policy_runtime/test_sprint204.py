"""Sprint 204 — Policy Foundation Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.policy_runtime.foundation.policy_descriptor import PolicyDescriptor
from sam.policy_runtime.foundation.policy_capability import PolicyCapability
from sam.policy_runtime.foundation.policy_contract import PolicyContract
from sam.policy_runtime.foundation.policy_metadata import PolicyMetadata
from sam.policy_runtime.foundation.policy_registry import PolicyRegistry
from sam.policy_runtime.foundation.conversation_policy import ConversationPolicyBridge
from sam.policy_runtime.foundation.dashboard_policy import DashboardPolicyBridge
from sam.policy_runtime.dashboard import PolicyCard


def _registry():
    r = PolicyRegistry()
    r.register(PolicyDescriptor("pol1", "AccessControl", category="security"))
    r.attach_capability(PolicyCapability("cap1", "pol1", operations=["represent"]))
    r.register(PolicyDescriptor("pol2", "Throttle", category="performance"))
    return r


class TestPolicyDescriptor:
    def test_basic(self):
        d = PolicyDescriptor("pol1", "AccessControl")
        assert d.id == "pol1"
        assert d.category == "policy"

    def test_empty_id_raises(self):
        with pytest.raises(ValueError):
            PolicyDescriptor("", "x")

    def test_tags_default(self):
        assert PolicyDescriptor("a", "b").tags == []

    def test_immutable(self):
        d = PolicyDescriptor("pol1", "AccessControl")
        with pytest.raises(FrozenInstanceError):
            d.name = "x"


class TestPolicyCapability:
    def test_supports(self):
        c = PolicyCapability("cap1", "pol1", operations=["represent", "list"])
        assert c.supports("represent") is True
        assert c.supports("other") is False

    def test_no_inference_default(self):
        assert PolicyCapability("c").no_inference is True

    def test_deterministic_default(self):
        assert PolicyCapability("c").deterministic is True

    def test_immutable(self):
        c = PolicyCapability("c")
        with pytest.raises(FrozenInstanceError):
            c.id = "x"


class TestPolicyContract:
    def test_default(self):
        c = PolicyContract("c1")
        assert c.preview_only is True
        assert c.version == "21.0.0"

    def test_hash_deterministic(self):
        c = PolicyContract("c1", "pol1", ["a", "b"])
        assert c.hash() == c.hash()

    def test_hash_different(self):
        a = PolicyContract("c1", "pol1", ["x"])
        b = PolicyContract("c1", "pol1", ["y"])
        assert a.hash() != b.hash()

    def test_immutable(self):
        c = PolicyContract("c1")
        with pytest.raises(FrozenInstanceError):
            c.version = "1"


class TestPolicyMetadata:
    def test_default_no_inference(self):
        assert PolicyMetadata().no_inference is True

    def test_default_preview(self):
        assert PolicyMetadata().preview_only is True

    def test_created_at_generated(self):
        assert PolicyMetadata().created_at != ""

    def test_immutable(self):
        m = PolicyMetadata()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestPolicyRegistry:
    def test_register_get(self):
        r = PolicyRegistry()
        r.register(PolicyDescriptor("pol1", "AccessControl"))
        assert r.get("pol1").name == "AccessControl"

    def test_exists(self):
        r = _registry()
        assert r.exists("pol1") is True
        assert r.exists("nope") is False

    def test_count(self):
        assert _registry().count() == 2

    def test_all(self):
        assert len(_registry().all()) == 2

    def test_capabilities(self):
        r = _registry()
        caps = r.capabilities("pol1")
        assert len(caps) == 1
        assert caps[0].id == "cap1"

    def test_missing_get(self):
        assert _registry().get("nope") is None


class TestConversationPolicyBridge:
    def test_summary(self):
        b = ConversationPolicyBridge(_registry())
        assert b.summary()["total_Policy"] == 2
        assert b.summary()["preview_only"] is True

    def test_status(self):
        b = ConversationPolicyBridge(_registry())
        assert b.status("pol1") == "registered"
        assert b.status("nope") == "missing"


class TestDashboardPolicyBridge:
    def test_five_cards(self):
        b = DashboardPolicyBridge(_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_overview(self):
        b = DashboardPolicyBridge(_registry())
        assert b.overview_card().verdict == "ready"


class TestFoundationImmutability:
    DTO_CLASSES = [
        PolicyDescriptor, PolicyCapability, PolicyContract,
        PolicyMetadata, PolicyCard,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
