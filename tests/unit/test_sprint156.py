"""Sprint 156 — Agent Foundation Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.agent.foundation.agent_descriptor import AgentDescriptor, AgentStatus, AgentSummary
from sam.agent.foundation.agent_capability import AgentCapability, AgentOperation
from sam.agent.foundation.agent_contract import AgentContract, AgentContractCompliance
from sam.agent.foundation.agent_metadata import AgentMetadata
from sam.agent.foundation.agent_registry import AgentRegistry, AgentRegistration
from sam.agent.foundation.conversation_foundation import ConversationFoundationBridge
from sam.agent.foundation.dashboard_foundation import DashboardFoundationBridge
from sam.agent.dashboard.agent_dashboard import ExecutionCard


def _ready_registry():
    r = AgentRegistry()
    r.register(AgentDescriptor("agent1", "Primary Agent", runtime_layer="agent"))
    r.attach_capability(AgentCapability(
        "cap1", "agent1", "lifecycle",
        operations=[AgentOperation("prepare"), AgentOperation("run")],
    ))
    r.attach_contract(AgentContract("ct1", "agent1", "agent-contract",
                                    guarantees=["preview-only"]))
    r.attach_metadata(AgentMetadata("agent1", author="SAM"))
    return r


class TestAgentDescriptor:
    def test_default(self):
        d = AgentDescriptor("a1")
        assert d.runtime_layer == "agent"
        assert d.implements == []

    def test_immutable(self):
        d = AgentDescriptor("a1")
        with pytest.raises(FrozenInstanceError):
            d.name = "x"


class TestAgentStatus:
    def test_default(self):
        assert AgentStatus("a1").state == "unknown"


class TestAgentSummary:
    def test_empty(self):
        assert AgentSummary().total_agents == 0


class TestAgentCapability:
    def test_supports(self):
        c = AgentCapability("c1", "a1", operations=[
            AgentOperation("prepare"), AgentOperation("run")])
        assert c.supports("prepare")
        assert not c.supports("delete")

    def test_immutable(self):
        c = AgentCapability("c1", "a1")
        with pytest.raises(FrozenInstanceError):
            c.name = "x"


class TestAgentOperation:
    def test_preview_default(self):
        assert AgentOperation("prepare").preview_only is True


class TestAgentContract:
    def test_default_guarantees(self):
        assert AgentContract("c1", "a1").guarantees == []

    def test_immutable(self):
        c = AgentContract("c1", "a1")
        with pytest.raises(FrozenInstanceError):
            c.name = "x"


class TestAgentContractCompliance:
    def test_default_compliant(self):
        assert AgentContractCompliance("c1", "a1").compliant is True


class TestAgentMetadata:
    def test_readonly_default(self):
        assert AgentMetadata("a1").readonly is True


class TestAgentRegistry:
    def test_register(self):
        r = _ready_registry()
        assert r.count() == 1
        assert r.list_ids() == ["agent1"]

    def test_duplicate_rejected(self):
        r = AgentRegistry()
        assert r.register(AgentDescriptor("a1"))
        assert not r.register(AgentDescriptor("a1"))

    def test_get(self):
        r = _ready_registry()
        assert r.get("agent1").agent_id == "agent1"

    def test_capabilities(self):
        r = _ready_registry()
        assert r.get_capabilities("agent1")[0].supports("prepare")

    def test_contract(self):
        r = _ready_registry()
        assert "preview-only" in r.get_contract("agent1").guarantees

    def test_metadata(self):
        r = _ready_registry()
        assert r.get_metadata("agent1").author == "SAM"

    def test_summary(self):
        r = _ready_registry()
        s = r.summary()
        assert s.total_agents == 1
        assert s.states["agent"] == 1


class TestConversationFoundationBridge:
    def test_show_agent_status(self):
        b = ConversationFoundationBridge(_ready_registry())
        assert b.show_agent_status() == {"registered": 1}

    def test_list(self):
        b = ConversationFoundationBridge(_ready_registry())
        assert b.list_agents() == ["agent1"]

    def test_describe(self):
        b = ConversationFoundationBridge(_ready_registry())
        assert b.describe("agent1") == "Primary Agent"

    def test_capability_names(self):
        b = ConversationFoundationBridge(_ready_registry())
        assert b.capability_names("agent1") == ["cap1"]


class TestDashboardFoundationBridge:
    def test_five_cards(self):
        b = DashboardFoundationBridge(_ready_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_card_verdict(self):
        b = DashboardFoundationBridge(_ready_registry())
        assert b.overview_card().verdict == "ready"


class TestAgentFoundationImmutability:
    DTO_CLASSES = [
        AgentDescriptor, AgentStatus, AgentSummary,
        AgentCapability, AgentOperation, AgentContract,
        AgentContractCompliance, AgentMetadata, AgentRegistration, ExecutionCard,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
