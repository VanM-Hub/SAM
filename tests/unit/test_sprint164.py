"""Sprint 164 — Skill Foundation Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.skills.foundation.skill_descriptor import SkillDescriptor
from sam.skills.foundation.skill_capability import SkillCapability
from sam.skills.foundation.skill_contract import SkillContract, SkillContractCompliance
from sam.skills.foundation.skill_metadata import SkillMetadata
from sam.skills.foundation.skill_registry import SkillRegistry, SkillRegistrySummary
from sam.skills.foundation.conversation_skill import ConversationSkillBridge
from sam.skills.foundation.dashboard_skill import DashboardSkillBridge
from sam.skills.dashboard.skill_dashboard import ExecutionCard


def _ready_registry():
    r = SkillRegistry()
    r.register(SkillDescriptor(
        id="skill1", name="Read File", category="filesystem", version="1.0.0",
    ))
    r.attach_capability(SkillCapability(
        "cap1", "skill1", "read", operations=["read", "exists"],
    ))
    r.attach_contract(SkillContract("ct1", "skill1", "skill-contract",
                                    guarantees=["preview-only"]))
    r.attach_metadata(SkillMetadata("skill1", author="SAM"))
    return r


class TestSkillDescriptor:
    def test_default(self):
        d = SkillDescriptor("s1")
        assert d.name == ""
        assert d.category == "general"
        assert d.version == "1.0.0"
        assert d.tags == []

    def test_fields(self):
        d = SkillDescriptor("s1", name="X", version="2.0", category="io",
                            author="a", tags=["t1"],
                            capabilities=["c"], inputs=["i"], outputs=["o"],
                            constraints=["no-exec"], metadata={"k": "v"})
        assert d.category == "io"
        assert d.metadata == {"k": "v"}

    def test_immutable(self):
        d = SkillDescriptor("s1")
        with pytest.raises(FrozenInstanceError):
            d.name = "x"


class TestSkillCapability:
    def test_supports(self):
        c = SkillCapability("c1", "s1", operations=["read"])
        assert c.supports("read")
        assert not c.supports("delete")

    def test_preview_default(self):
        assert SkillCapability("c1", "s1").preview_only is True

    def test_immutable(self):
        c = SkillCapability("c1", "s1")
        with pytest.raises(FrozenInstanceError):
            c.name = "x"


class TestSkillContract:
    def test_default(self):
        assert SkillContract("ct1", "s1").guarantees == []

    def test_immutable(self):
        c = SkillContract("ct1", "s1")
        with pytest.raises(FrozenInstanceError):
            c.name = "x"


class TestSkillContractCompliance:
    def test_default(self):
        assert SkillContractCompliance("ct1", "s1").compliant is True


class TestSkillMetadata:
    def test_readonly(self):
        assert SkillMetadata("s1").readonly is True

    def test_immutable(self):
        m = SkillMetadata("s1")
        with pytest.raises(FrozenInstanceError):
            m.author = "x"


class TestSkillRegistry:
    def test_register_find(self):
        r = _ready_registry()
        assert r.exists("skill1")
        assert r.find("skill1").name == "Read File"

    def test_list(self):
        r = _ready_registry()
        assert r.list_ids() == ["skill1"]

    def test_duplicate_rejected(self):
        r = SkillRegistry()
        assert r.register(SkillDescriptor("s1"))
        assert not r.register(SkillDescriptor("s1"))

    def test_exists_missing(self):
        assert SkillRegistry().exists("nope") is False

    def test_capabilities(self):
        r = _ready_registry()
        assert r.get_capabilities("skill1")[0].supports("read")

    def test_contract(self):
        r = _ready_registry()
        assert "preview-only" in r.get_contract("skill1").guarantees

    def test_metadata(self):
        r = _ready_registry()
        assert r.get_metadata("skill1").author == "SAM"

    def test_summary(self):
        r = _ready_registry()
        s = r.summary()
        assert s.total == 1
        assert s.by_category["filesystem"] == 1


class TestSkillRegistrySummary:
    def test_default(self):
        assert SkillRegistrySummary().total == 0


class TestConversationSkillBridge:
    def test_summary(self):
        b = ConversationSkillBridge(_ready_registry())
        assert b.summary()["total"] == 1

    def test_registry(self):
        b = ConversationSkillBridge(_ready_registry())
        assert b.registry() == ["skill1"]

    def test_descriptor(self):
        b = ConversationSkillBridge(_ready_registry())
        assert b.descriptor("skill1") == "Read File"

    def test_metadata(self):
        b = ConversationSkillBridge(_ready_registry())
        assert b.metadata("skill1")["author"] == "SAM"

    def test_capability(self):
        b = ConversationSkillBridge(_ready_registry())
        assert b.capability("skill1") == ["cap1"]


class TestDashboardSkillBridge:
    def test_five_cards(self):
        b = DashboardSkillBridge(_ready_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardSkillBridge(_ready_registry())
        assert b.overview_card().verdict == "ready"


class TestSkillFoundationImmutability:
    DTO_CLASSES = [
        SkillDescriptor, SkillCapability, SkillContract,
        SkillContractCompliance, SkillMetadata, SkillRegistrySummary, ExecutionCard,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
