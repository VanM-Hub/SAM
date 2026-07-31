"""Sprint 197 — Workflow Model Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.workflow_runtime.model.workflow import Workflow
from sam.workflow_runtime.model.workflow_step import WorkflowStep
from sam.workflow_runtime.model.workflow_dependency import WorkflowDependency
from sam.workflow_runtime.model.workflow_constraint import WorkflowConstraint
from sam.workflow_runtime.model.workflow_validator import (
    WorkflowValidator, WorkflowValidation,
)
from sam.workflow_runtime.model.conversation_model import ConversationModelBridge
from sam.workflow_runtime.model.dashboard_model import DashboardModelBridge
from sam.workflow_runtime.dashboard import WorkflowCard


class TestWorkflow:
    def test_default(self):
        wf = Workflow("w1")
        assert wf.step_count() == 0
        assert wf.scope == "process"

    def test_preview_only(self):
        assert Workflow("w1").preview_only is True

    def test_steps(self):
        wf = Workflow("w1", steps=["s1", "s2"])
        assert wf.step_count() == 2

    def test_immutable(self):
        wf = Workflow("w1")
        with pytest.raises(FrozenInstanceError):
            wf.workflow_id = "x"


class TestWorkflowStep:
    def test_basic(self):
        s = WorkflowStep("s1", "w1", name="start", order=0)
        assert s.step_id == "s1"
        assert s.workflow_id == "w1"
        assert s.order == 0

    def test_preview_only(self):
        assert WorkflowStep("s1").preview_only is True

    def test_immutable(self):
        s = WorkflowStep("s1")
        with pytest.raises(FrozenInstanceError):
            s.order = 1


class TestWorkflowDependency:
    def test_ok(self):
        d = WorkflowDependency("d1", from_step="s1", to_step="s2")
        assert d.ok() is True

    def test_not_ok(self):
        d = WorkflowDependency("d1")
        assert d.ok() is False

    def test_immutable(self):
        d = WorkflowDependency("d1")
        with pytest.raises(FrozenInstanceError):
            d.from_step = "x"


class TestWorkflowConstraint:
    def test_default(self):
        c = WorkflowConstraint("c1")
        assert c.kind == "order"
        assert c.is_satisfied() is True

    def test_preview_only(self):
        assert WorkflowConstraint("c1").preview_only is True

    def test_immutable(self):
        c = WorkflowConstraint("c1")
        with pytest.raises(FrozenInstanceError):
            c.kind = "x"


class TestWorkflowValidator:
    def test_valid_workflow(self):
        v = WorkflowValidator().validate_workflow(Workflow("w1"))
        assert v.valid is True
        assert v.issues == []

    def test_workflow_no_id(self):
        v = WorkflowValidator().validate_workflow(Workflow(""))
        assert v.valid is False
        assert "workflow_id is required" in v.issues

    def test_valid_step(self):
        v = WorkflowValidator().validate_step(WorkflowStep("s1", "w1"))
        assert v.valid is True

    def test_step_no_workflow(self):
        v = WorkflowValidator().validate_step(WorkflowStep("s1"))
        assert v.valid is False

    def test_valid_dependency(self):
        v = WorkflowValidator().validate_dependency(
            WorkflowDependency("d1", from_step="s1", to_step="s2")
        )
        assert v.valid is True

    def test_invalid_dependency(self):
        v = WorkflowValidator().validate_dependency(WorkflowDependency("d1"))
        assert v.valid is False

    def test_valid_constraint(self):
        v = WorkflowValidator().validate_constraint(WorkflowConstraint("c1"))
        assert v.valid is True

    def test_invalid_constraint(self):
        v = WorkflowValidator().validate_constraint(WorkflowConstraint(""))
        assert v.valid is False


class TestWorkflowValidation:
    def test_default(self):
        assert WorkflowValidation().valid is True

    def test_immutable(self):
        val = WorkflowValidation()
        with pytest.raises(FrozenInstanceError):
            val.valid = False


class TestConversationModelBridge:
    def test_build_workflow(self):
        b = ConversationModelBridge()
        wf = b.build_workflow("w1", "Onboard")
        assert wf.workflow_id == "w1"
        assert wf.name == "Onboard"

    def test_build_step(self):
        b = ConversationModelBridge()
        s = b.build_step("s1", "w1")
        assert s.workflow_id == "w1"

    def test_is_valid(self):
        b = ConversationModelBridge()
        assert b.is_valid(Workflow("w1")) is True
        assert b.is_valid(Workflow("")) is False

    def test_summary(self):
        b = ConversationModelBridge()
        wf = Workflow("w1", steps=["s1"])
        assert b.summary(wf)["step_count"] == 1


class TestDashboardModelBridge:
    def test_five_cards(self):
        b = DashboardModelBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, WorkflowCard) for c in cards)

    def test_overview(self):
        b = DashboardModelBridge()
        assert b.overview_card().group == "model"


class TestModelImmutability:
    DTO_CLASSES = [
        Workflow, WorkflowStep, WorkflowDependency, WorkflowConstraint,
        WorkflowValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
