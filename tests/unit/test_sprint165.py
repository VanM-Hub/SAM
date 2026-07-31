"""Sprint 165 — Skill Definition Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.skills.definition.skill_definition import SkillDefinition
from sam.skills.definition.skill_input import SkillInput
from sam.skills.definition.skill_output import SkillOutput
from sam.skills.definition.skill_parameter import SkillParameter
from sam.skills.definition.skill_constraint import SkillConstraint
from sam.skills.definition.skill_validator import SkillValidator, SkillValidation
from sam.skills.definition.conversation_definition import ConversationDefinitionBridge
from sam.skills.definition.dashboard_definition import DashboardDefinitionBridge
from sam.skills.dashboard.skill_dashboard import ExecutionCard


def _definition():
    return SkillDefinition(
        definition_id="def1", skill_id="skill1",
        inputs=[SkillInput("path", "string", required=True)],
        outputs=[SkillOutput("content", "string")],
        constraints=[SkillConstraint("preview-only")],
    )


class TestSkillDefinition:
    def test_counts(self):
        d = _definition()
        assert d.input_count == 1
        assert d.output_count == 1

    def test_immutable(self):
        d = SkillDefinition("def1")
        with pytest.raises(FrozenInstanceError):
            d.skill_id = "x"


class TestSkillInput:
    def test_default(self):
        i = SkillInput("path")
        assert i.input_type == "string"
        assert i.required is False

    def test_immutable(self):
        i = SkillInput("path")
        with pytest.raises(FrozenInstanceError):
            i.required = True


class TestSkillOutput:
    def test_default(self):
        assert SkillOutput("out").output_type == "string"

    def test_immutable(self):
        o = SkillOutput("out")
        with pytest.raises(FrozenInstanceError):
            o.output_type = "int"


class TestSkillParameter:
    def test_default(self):
        assert SkillParameter("p").allowed_values == []

    def test_immutable(self):
        p = SkillParameter("p")
        with pytest.raises(FrozenInstanceError):
            p.required = True


class TestSkillConstraint:
    def test_default(self):
        assert SkillConstraint("c").allowed is True

    def test_immutable(self):
        c = SkillConstraint("c")
        with pytest.raises(FrozenInstanceError):
            c.allowed = False


class TestSkillValidator:
    def test_valid(self):
        v = SkillValidator().validate(_definition())
        assert v.valid is True

    def test_missing_ids(self):
        v = SkillValidator().validate(SkillDefinition(""))
        assert v.valid is False

    def test_validate_inputs(self):
        v = SkillValidator().validate_inputs([SkillInput("a"), SkillInput("")])
        assert v.valid is False

    def test_validate_outputs(self):
        v = SkillValidator().validate_outputs([SkillOutput("ok")])
        assert v.valid is True

    def test_validate_constraints(self):
        v = SkillValidator().validate_constraints([SkillConstraint("x")])
        assert v.valid is True


class TestSkillValidation:
    def test_default(self):
        assert SkillValidation().valid is True


class TestConversationDefinitionBridge:
    def test_summary(self):
        b = ConversationDefinitionBridge(_definition())
        s = b.summary()
        assert s["has_definition"] is True
        assert s["inputs"] == 1

    def test_validity(self):
        b = ConversationDefinitionBridge(_definition())
        assert b.validity()["valid"] is True

    def test_no_definition(self):
        b = ConversationDefinitionBridge()
        assert b.summary()["has_definition"] is False


class TestDashboardDefinitionBridge:
    def test_five_cards(self):
        b = DashboardDefinitionBridge(_definition())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardDefinitionBridge(_definition())
        assert b.overview_card().verdict == "ready"


class TestDefinitionImmutability:
    DTO_CLASSES = [
        SkillDefinition, SkillInput, SkillOutput,
        SkillParameter, SkillConstraint, SkillValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
