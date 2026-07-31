"""Sprint 166 — Skill Builder Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.skills.builder.skill_builder import SkillBuilder, SkillBuildResult
from sam.skills.builder.workflow_builder import WorkflowBuilder, SkillWorkflow
from sam.skills.builder.step_builder import StepBuilder, SkillStep
from sam.skills.builder.parameter_builder import ParameterBuilder
from sam.skills.builder.preview_builder import PreviewBuilder, SkillPreview
from sam.skills.builder.conversation_builder import ConversationBuilderBridge
from sam.skills.builder.dashboard_builder import DashboardBuilderBridge
from sam.skills.dashboard.skill_dashboard import ExecutionCard


class TestSkillBuilder:
    def test_build(self):
        res = SkillBuilder().build("skill1", name="Read", category="io")
        assert res.valid is True
        assert res.descriptor.id == "skill1"
        assert res.descriptor.category == "io"
        assert res.definition.skill_id == "skill1"

    def test_build_missing_id(self):
        res = SkillBuilder().build("")
        assert res.valid is False

    def test_default_name(self):
        res = SkillBuilder().build("s1")
        assert res.descriptor.name == "s1"


class TestSkillBuildResult:
    def test_default(self):
        assert SkillBuildResult().valid is False


class TestWorkflowBuilder:
    def test_build(self):
        w = WorkflowBuilder().build("wf1", "skill1")
        assert w.workflow_id == "wf1"
        assert w.skill_id == "skill1"
        assert w.step_count == 0

    def test_immutable(self):
        w = SkillWorkflow("wf1")
        with pytest.raises(FrozenInstanceError):
            w.skill_id = "x"


class TestStepBuilder:
    def test_build(self):
        s = StepBuilder().build("step1", "skill1", order=0, action="read",
                                inputs={"path": "/a"})
        assert s.action == "read"
        assert s.inputs == {"path": "/a"}
        assert s.preview_only is True

    def test_preview_default(self):
        assert StepBuilder().build("s1", "sk").preview_only is True

    def test_immutable(self):
        s = SkillStep("s1", "sk")
        with pytest.raises(FrozenInstanceError):
            s.action = "run"


class TestParameterBuilder:
    def test_build(self):
        p = ParameterBuilder().build("path", "string", required=True)
        assert p.name == "path"
        assert p.required is True

    def test_build_many(self):
        ps = ParameterBuilder().build_many(["a", "b"])
        assert len(ps) == 2


class TestPreviewBuilder:
    def test_build(self):
        p = PreviewBuilder().build("pv1", "skill1", steps=["read"])
        assert p.preview is True
        assert p.executed is False
        assert p.external_calls == 0
        assert p.steps == ["read"]

    def test_external_always_zero(self):
        p = PreviewBuilder().build("pv1", "s1")
        assert p.external_calls == 0

    def test_immutable(self):
        p = SkillPreview("pv1")
        with pytest.raises(FrozenInstanceError):
            p.executed = True


class TestConversationBuilderBridge:
    def test_summary_valid(self):
        b = ConversationBuilderBridge()
        assert b.summary("s1")["valid"] is True

    def test_summary_invalid(self):
        b = ConversationBuilderBridge()
        assert b.summary("")["valid"] is False

    def test_describe(self):
        b = ConversationBuilderBridge()
        assert "build-only" in b.describe_builder()


class TestDashboardBuilderBridge:
    def test_five_cards(self):
        b = DashboardBuilderBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardBuilderBridge()
        assert b.overview_card().verdict == "ready"


class TestBuilderImmutability:
    DTO_CLASSES = [
        SkillBuildResult, SkillWorkflow, SkillStep, SkillPreview,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
