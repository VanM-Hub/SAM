"""Sprint 196 — Workflow Foundation Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.workflow_runtime.foundation.workflow_descriptor import WorkflowDescriptor
from sam.workflow_runtime.foundation.workflow_capability import WorkflowCapability
from sam.workflow_runtime.foundation.workflow_contract import WorkflowContract
from sam.workflow_runtime.foundation.workflow_metadata import WorkflowMetadata
from sam.workflow_runtime.foundation.workflow_registry import WorkflowRegistry
from sam.workflow_runtime.foundation.conversation_workflow import ConversationWorkflowBridge
from sam.workflow_runtime.foundation.dashboard_workflow import DashboardWorkflowBridge
from sam.workflow_runtime.dashboard import WorkflowCard


def _registry():
    r = WorkflowRegistry()
    r.register(WorkflowDescriptor("wf1", "Onboard", category="process"))
    r.attach_capability(WorkflowCapability("cap1", "wf1", operations=["compose"]))
    r.register(WorkflowDescriptor("wf2", "Deploy", category="process"))
    return r


class TestWorkflowDescriptor:
    def test_basic(self):
        d = WorkflowDescriptor("wf1", "Onboard")
        assert d.id == "wf1"
        assert d.category == "workflow"

    def test_empty_id_raises(self):
        with pytest.raises(ValueError):
            WorkflowDescriptor("", "x")

    def test_tags_default(self):
        assert WorkflowDescriptor("a", "b").tags == []

    def test_immutable(self):
        d = WorkflowDescriptor("wf1", "Onboard")
        with pytest.raises(FrozenInstanceError):
            d.name = "x"


class TestWorkflowCapability:
    def test_supports(self):
        c = WorkflowCapability("cap1", "wf1", operations=["compose", "plan"])
        assert c.supports("compose") is True
        assert c.supports("other") is False

    def test_no_inference_default(self):
        assert WorkflowCapability("c").no_inference is True

    def test_deterministic_default(self):
        assert WorkflowCapability("c").deterministic is True

    def test_immutable(self):
        c = WorkflowCapability("c")
        with pytest.raises(FrozenInstanceError):
            c.id = "x"


class TestWorkflowContract:
    def test_default(self):
        c = WorkflowContract("c1")
        assert c.preview_only is True
        assert c.version == "20.0.0"

    def test_hash_deterministic(self):
        c = WorkflowContract("c1", "wf1", ["a", "b"])
        assert c.hash() == c.hash()

    def test_hash_different(self):
        a = WorkflowContract("c1", "wf1", ["x"])
        b = WorkflowContract("c1", "wf1", ["y"])
        assert a.hash() != b.hash()

    def test_immutable(self):
        c = WorkflowContract("c1")
        with pytest.raises(FrozenInstanceError):
            c.version = "1"


class TestWorkflowMetadata:
    def test_default_no_inference(self):
        assert WorkflowMetadata().no_inference is True

    def test_default_preview(self):
        assert WorkflowMetadata().preview_only is True

    def test_created_at_generated(self):
        assert WorkflowMetadata().created_at != ""

    def test_immutable(self):
        m = WorkflowMetadata()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestWorkflowRegistry:
    def test_register_get(self):
        r = WorkflowRegistry()
        r.register(WorkflowDescriptor("wf1", "Onboard"))
        assert r.get("wf1").name == "Onboard"

    def test_exists(self):
        r = _registry()
        assert r.exists("wf1") is True
        assert r.exists("nope") is False

    def test_count(self):
        assert _registry().count() == 2

    def test_all(self):
        assert len(_registry().all()) == 2

    def test_capabilities(self):
        r = _registry()
        caps = r.capabilities("wf1")
        assert len(caps) == 1
        assert caps[0].id == "cap1"

    def test_missing_get(self):
        assert _registry().get("nope") is None


class TestConversationWorkflowBridge:
    def test_summary(self):
        b = ConversationWorkflowBridge(_registry())
        assert b.summary()["total_Workflow"] == 2
        assert b.summary()["preview_only"] is True

    def test_status(self):
        b = ConversationWorkflowBridge(_registry())
        assert b.status("wf1") == "registered"
        assert b.status("nope") == "missing"


class TestDashboardWorkflowBridge:
    def test_five_cards(self):
        b = DashboardWorkflowBridge(_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, WorkflowCard) for c in cards)

    def test_overview(self):
        b = DashboardWorkflowBridge(_registry())
        assert b.overview_card().verdict == "ready"


class TestFoundationImmutability:
    DTO_CLASSES = [
        WorkflowDescriptor, WorkflowCapability, WorkflowContract,
        WorkflowMetadata, WorkflowCard,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
