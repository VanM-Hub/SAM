"""Sprint 205 — Policy Model Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.policy_runtime.model.policy import Policy
from sam.policy_runtime.model.policy_rule import PolicyRule
from sam.policy_runtime.model.policy_scope import PolicyScope, VALID_SCOPES
from sam.policy_runtime.model.policy_constraint import PolicyConstraint
from sam.policy_runtime.model.policy_validator import (
    PolicyValidator, PolicyValidation,
)
from sam.policy_runtime.model.conversation_model import ConversationModelBridge
from sam.policy_runtime.model.dashboard_model import DashboardModelBridge
from sam.policy_runtime.dashboard import PolicyCard


class TestPolicy:
    def test_default(self):
        pol = Policy("pol1")
        assert pol.rule_count() == 0
        assert pol.scope == "system"

    def test_preview_only(self):
        assert Policy("pol1").preview_only is True

    def test_rules(self):
        pol = Policy("pol1", rules=["r1", "r2"])
        assert pol.rule_count() == 2

    def test_immutable(self):
        pol = Policy("pol1")
        with pytest.raises(FrozenInstanceError):
            pol.policy_id = "x"


class TestPolicyRule:
    def test_basic(self):
        r = PolicyRule("r1", "pol1", kind="deny")
        assert r.rule_id == "r1"
        assert r.policy_id == "pol1"
        assert r.kind == "deny"

    def test_preview_only(self):
        assert PolicyRule("r1").preview_only is True

    def test_immutable(self):
        r = PolicyRule("r1")
        with pytest.raises(FrozenInstanceError):
            r.kind = "x"


class TestPolicyScope:
    def test_default(self):
        s = PolicyScope()
        assert s.scope == "system"

    def test_valid_scopes(self):
        assert VALID_SCOPES == ["system", "mission", "workflow", "resource", "user"]

    def test_invalid_scope(self):
        with pytest.raises(ValueError):
            PolicyScope(scope="bad")

    def test_immutable(self):
        s = PolicyScope()
        with pytest.raises(FrozenInstanceError):
            s.scope = "user"


class TestPolicyConstraint:
    def test_default(self):
        c = PolicyConstraint("c1")
        assert c.kind == "condition"
        assert c.preview_only is True

    def test_immutable(self):
        c = PolicyConstraint("c1")
        with pytest.raises(FrozenInstanceError):
            c.kind = "x"


class TestPolicyValidator:
    def test_valid_policy(self):
        v = PolicyValidator().validate_policy(Policy("pol1"))
        assert v.valid is True
        assert v.issues == []

    def test_policy_no_id(self):
        v = PolicyValidator().validate_policy(Policy(""))
        assert v.valid is False
        assert "policy_id is required" in v.issues

    def test_valid_rule(self):
        v = PolicyValidator().validate_rule(PolicyRule("r1", "pol1"))
        assert v.valid is True

    def test_rule_no_id(self):
        v = PolicyValidator().validate_rule(PolicyRule(""))
        assert v.valid is False

    def test_valid_scope(self):
        v = PolicyValidator().validate_scope(PolicyScope("user"))
        assert v.valid is True

    def test_scope_invalid_impossible(self):
        # konstruktor PolicyScope menolak scope invalid, jadi validator selalu valid
        assert PolicyValidator().validate_scope(PolicyScope("system")).valid is True

    def test_valid_constraint(self):
        v = PolicyValidator().validate_constraint(PolicyConstraint("c1"))
        assert v.valid is True

    def test_invalid_constraint(self):
        v = PolicyValidator().validate_constraint(PolicyConstraint(""))
        assert v.valid is False


class TestPolicyValidation:
    def test_default(self):
        assert PolicyValidation().valid is True

    def test_immutable(self):
        val = PolicyValidation()
        with pytest.raises(FrozenInstanceError):
            val.valid = False


class TestConversationModelBridge:
    def test_build_policy(self):
        b = ConversationModelBridge()
        pol = b.build_policy("pol1", "Access Control")
        assert pol.policy_id == "pol1"
        assert pol.name == "Access Control"

    def test_build_rule(self):
        b = ConversationModelBridge()
        r = b.build_rule("r1", "pol1")
        assert r.policy_id == "pol1"

    def test_is_valid(self):
        b = ConversationModelBridge()
        assert b.is_valid(Policy("pol1")) is True
        assert b.is_valid(Policy("")) is False

    def test_summary(self):
        b = ConversationModelBridge()
        pol = Policy("pol1", rules=["r1"])
        assert b.summary(pol)["rule_count"] == 1


class TestDashboardModelBridge:
    def test_five_cards(self):
        b = DashboardModelBridge()
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_overview(self):
        b = DashboardModelBridge()
        assert b.overview_card().group == "model"


class TestModelImmutability:
    DTO_CLASSES = [
        Policy, PolicyRule, PolicyScope, PolicyConstraint, PolicyValidation,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
