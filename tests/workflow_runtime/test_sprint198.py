"""Sprint 198 — Workflow Builder Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.workflow_runtime.builder.workflow_builder import (
    WorkflowBuilder, WorkflowBuildResult,
)
from sam.workflow_runtime.builder.step_builder import StepBuilder
from sam.workflow_runtime.builder.dependency_builder import DependencyBuilder
from sam.workflow_runtime.builder.constraint_builder import ConstraintBuilder
from sam.workflow_runtime.builder.preview_builder import (
    PreviewBuilder, WorkflowPreviewDTO,
)
from sam.workflow_runtime.builder.conversation_builder import ConversationBuilderBridge
from sam.workflow_runtime.builder.dashboard_builder import DashboardBuilderBridge
from sam.workflow_runtime.model.workflow import Workflow
from sam.workflow_runtime.model.workflow_step import WorkflowStep
from sam.workflow_runtime.model.workflow_dependency import WorkflowDependency
from sam.workflow_runtime.model.workflow_constraint import WorkflowConstraint
from sam.workflow_runtime.dashboard import WorkflowCard


class TestWorkflowBuilder:
    def test_build(self):
        r = WorkflowBuilder().build("w1", "Onboard")
        assert r.ok is True
        assert r.workflow.workflow_id == "w1"
        assert r.workflow.name == "Onboard"

    def test_build_steps(self):
        r = WorkflowBuilder().build("w1", steps=["s1", "s2"])
        assert r.workflow.step_count() == 2

    def test_result_default(self):
        assert WorkflowBuildResult().ok is True

    def test_result_immutable(self):
        r = WorkflowBuildResult()
        with pytest.raises(FrozenInstanceError):
            r.ok = False


class TestStepBuilder:
    def test_build(self):
        s = StepBuilder().build("s1", "w1", order=1)
        assert s.step_id == "s1"
        assert s.workflow_id == "w1"
        assert s.order == 1

    def test_build_default_order(self):
        s = StepBuilder().build("s1", "w1")
        assert s.order == 0

    def test_build_kind_default(self):
        s = StepBuilder().build("s1", "w1")
        assert s.kind == "compose"

    def test_build_preview_only(self):
        s = StepBuilder().build("s1", "w1")
        assert s.preview_only is True

    def test_build_is_workflow_step(self):
        s = StepBuilder().build("s1", "w1")
        assert isinstance(s, WorkflowStep)


class TestDependencyBuilder:
    def test_build(self):
        d = DependencyBuilder().build("d1", "s1", "s2")
        assert d.ok() is True
        assert d.from_step == "s1"

    def test_build_to_step(self):
        d = DependencyBuilder().build("d1", "s1", "s2")
        assert d.to_step == "s2"

    def test_is_workflow_dependency(self):
        d = DependencyBuilder().build("d1", "s1", "s2")
        assert isinstance(d, WorkflowDependency)


class TestConstraintBuilder:
    def test_build(self):
        c = ConstraintBuilder().build("c1", kind="order")
        assert c.constraint_id == "c1"
        assert c.kind == "order"

    def test_build_default_kind(self):
        c = ConstraintBuilder().build("c1")
        assert c.kind == "order"

    def test_build_expression(self):
        c = ConstraintBuilder().build("c1", expression="a<b")
        assert c.expression == "a<b"

    def test_build_satisfied(self):
        c = ConstraintBuilder().build("c1")
        assert c.is_satisfied() is True

    def test_is_workflow_constraint(self):
        c = ConstraintBuilder().build("c1")
        assert isinstance(c, WorkflowConstraint)


class TestPreviewBuilder:
    def test_build(self):
        p = PreviewBuilder().build("label", Workflow("w1"))
        assert p.label == "label"
        assert p.composed is True

    def test_no_schedule_default(self):
        p = PreviewBuilder().build("l", Workflow("w1"))
        assert p.scheduled is False
        assert p.external_calls == 0

    def test_forbid_schedule(self):
        with pytest.raises(ValueError):
            WorkflowPreviewDTO(label="l", scheduled=True)

    def test_forbid_external(self):
        with pytest.raises(ValueError):
            WorkflowPreviewDTO(label="l", external_calls=1)

    def test_default_workflow(self):
        p = WorkflowPreviewDTO(label="l")
        assert p.workflow.workflow_id == ""

    def test_preview_dto_immutable(self):
        p = WorkflowPreviewDTO()
        with pytest.raises(FrozenInstanceError):
            p.label = "x"


class TestConversationBuilderBridge:
    def test_5_queries(self):
        b = ConversationBuilderBridge()
        wf = b.query_1_workflow("w1")
        assert wf.workflow_id == "w1"
        s = b.query_2_step("s1", "w1")
        assert isinstance(s, WorkflowStep)
        d = b.query_3_dependency("d1", "s1", "s2")
        assert isinstance(d, WorkflowDependency)
        c = b.query_4_constraint("c1")
        assert isinstance(c, WorkflowConstraint)
        p = b.query_5_preview("l", wf)
        assert p.scheduled is False


class TestDashboardBuilderBridge:
    def test_five_cards(self):
        b = DashboardBuilderBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, WorkflowCard) for c in cards)

    def test_overview(self):
        b = DashboardBuilderBridge()
        assert b.overview_card().group == "builder"


class TestBuilderImmutability:
    DTO_CLASSES = [
        WorkflowBuildResult, WorkflowPreviewDTO,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
