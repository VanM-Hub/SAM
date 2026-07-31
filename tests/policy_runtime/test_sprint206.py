"""Sprint 206 — Policy Builder Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.policy_runtime.builder.policy_builder import (
    PolicyBuilder, PolicyBuildResult,
)
from sam.policy_runtime.builder.rule_builder import RuleBuilder
from sam.policy_runtime.builder.scope_builder import ScopeBuilder
from sam.policy_runtime.builder.constraint_builder import ConstraintBuilder
from sam.policy_runtime.builder.preview_builder import (
    PreviewBuilder, PolicyPreviewDTO,
)
from sam.policy_runtime.builder.conversation_builder import ConversationBuilderBridge
from sam.policy_runtime.builder.dashboard_builder import DashboardBuilderBridge
from sam.policy_runtime.model.policy import Policy
from sam.policy_runtime.model.policy_rule import PolicyRule
from sam.policy_runtime.model.policy_scope import PolicyScope
from sam.policy_runtime.model.policy_constraint import PolicyConstraint
from sam.policy_runtime.dashboard import PolicyCard


class TestPolicyBuilder:
    def test_build(self):
        r = PolicyBuilder().build("pol1", "AccessControl")
        assert r.ok is True
        assert r.policy.policy_id == "pol1"
        assert r.policy.name == "AccessControl"

    def test_build_rules(self):
        r = PolicyBuilder().build("pol1", rules=["r1", "r2"])
        assert r.policy.rule_count() == 2

    def test_result_default(self):
        assert PolicyBuildResult().ok is True

    def test_result_immutable(self):
        r = PolicyBuildResult()
        with pytest.raises(FrozenInstanceError):
            r.ok = False


class TestRuleBuilder:
    def test_build(self):
        r = RuleBuilder().build("r1", "pol1", kind="deny")
        assert r.rule_id == "r1"
        assert r.policy_id == "pol1"
        assert r.kind == "deny"

    def test_default_kind(self):
        assert RuleBuilder().build("r1", "pol1").kind == "allow"

    def test_preview_only(self):
        assert RuleBuilder().build("r1", "pol1").preview_only is True

    def test_is_policy_rule(self):
        assert isinstance(RuleBuilder().build("r1", "pol1"), PolicyRule)


class TestScopeBuilder:
    def test_build(self):
        s = ScopeBuilder().build("user", ["u1"])
        assert s.scope == "user"
        assert s.targets == ["u1"]

    def test_default_scope(self):
        assert ScopeBuilder().build().scope == "system"

    def test_is_policy_scope(self):
        assert isinstance(ScopeBuilder().build(), PolicyScope)


class TestConstraintBuilder:
    def test_build(self):
        c = ConstraintBuilder().build("c1", kind="bound")
        assert c.constraint_id == "c1"
        assert c.kind == "bound"

    def test_default_kind(self):
        assert ConstraintBuilder().build("c1").kind == "condition"

    def test_expression(self):
        c = ConstraintBuilder().build("c1", expression="x<3")
        assert c.expression == "x<3"

    def test_is_policy_constraint(self):
        assert isinstance(ConstraintBuilder().build("c1"), PolicyConstraint)


class TestPreviewBuilder:
    def test_build(self):
        p = PreviewBuilder().build("label", Policy("pol1"))
        assert p.label == "label"
        assert p.composed is True

    def test_no_decision_default(self):
        p = PreviewBuilder().build("l", Policy("pol1"))
        assert p.decided is False
        assert p.external_calls == 0

    def test_forbid_decision(self):
        with pytest.raises(ValueError):
            PolicyPreviewDTO(label="l", decided=True)

    def test_forbid_external(self):
        with pytest.raises(ValueError):
            PolicyPreviewDTO(label="l", external_calls=1)

    def test_default_policy(self):
        p = PolicyPreviewDTO(label="l")
        assert p.policy.policy_id == ""

    def test_preview_dto_immutable(self):
        p = PolicyPreviewDTO()
        with pytest.raises(FrozenInstanceError):
            p.label = "x"


class TestConversationBuilderBridge:
    def test_5_queries(self):
        b = ConversationBuilderBridge()
        pol = b.query_1_policy("pol1")
        assert pol.policy_id == "pol1"
        r = b.query_2_rule("r1", "pol1")
        assert isinstance(r, PolicyRule)
        s = b.query_3_scope("user")
        assert isinstance(s, PolicyScope)
        c = b.query_4_constraint("c1")
        assert isinstance(c, PolicyConstraint)
        p = b.query_5_preview("l", pol)
        assert p.decided is False


class TestDashboardBuilderBridge:
    def test_five_cards(self):
        b = DashboardBuilderBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_overview(self):
        b = DashboardBuilderBridge()
        assert b.overview_card().group == "builder"


class TestBuilderImmutability:
    DTO_CLASSES = [
        PolicyBuildResult, PolicyPreviewDTO,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
