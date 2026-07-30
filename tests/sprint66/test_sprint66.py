import pytest, os, sys
from dataclasses import FrozenInstanceError
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.approval.policy import ApprovalPolicy, PolicyEffect, PolicyCondition, PolicyEvaluationResult
from sam.approval.policy_engine import PolicyEngine
from sam.approval.policy_builder import PolicyBuilder
from sam.approval.policy_validator import PolicyValidator

def test_policy_frozen():
    p = ApprovalPolicy(policy_id="p1")
    with pytest.raises(FrozenInstanceError): p.policy_id = "x"

def test_policy_builder():
    p = PolicyBuilder.build("p1", "High Risk", "require_review", [{"field":"score","operator":"lt","value":"0.5"}])
    assert p.policy_id == "p1"
    assert p.effect == PolicyEffect.REQUIRE_REVIEW

def test_policy_defaults():
    ps = PolicyBuilder.default_policies()
    assert len(ps) == 3

def test_engine_register():
    e = PolicyEngine()
    e.register(ApprovalPolicy(policy_id="p1", name="Test", effect=PolicyEffect.DENY))
    assert e.policy_count == 1

def test_evaluate_match():
    e = PolicyEngine()
    e.register(ApprovalPolicy(policy_id="p1", name="Risk", effect=PolicyEffect.REQUIRE_REVIEW,
        conditions=[PolicyCondition(field="risk", operator="eq", value="high")]))
    r = e.evaluate("p1", {"risk":"high"})
    assert r.match is True

def test_evaluate_nomatch():
    e = PolicyEngine()
    e.register(ApprovalPolicy(policy_id="p1", name="Risk", effect=PolicyEffect.DENY,
        conditions=[PolicyCondition(field="risk", operator="eq", value="high")]))
    r = e.evaluate("p1", {"risk":"low"})
    assert r.match is False

def test_evaluate_notfound():
    r = PolicyEngine().evaluate("x", {})
    assert r.match is False

def test_evaluate_all():
    e = PolicyEngine()
    for p in PolicyBuilder.default_policies(): e.register(p)
    rs = e.evaluate_all({"readiness_score":"0.9","certified":"True"})
    assert len(rs) >= 1

def test_validator_valid():
    v, e = PolicyValidator.validate(ApprovalPolicy(policy_id="p1", name="T"))
    assert v is True

def test_validator_invalid():
    v, e = PolicyValidator.validate(ApprovalPolicy(policy_id="", name=""))
    assert v is False

def test_condition_eq():
    e = PolicyEngine()
    c = PolicyCondition(field="x", operator="eq", value="1")
    assert e._match_condition(c, {"x":"1"}) is True
    assert e._match_condition(c, {"x":"2"}) is False

def test_condition_in():
    e = PolicyEngine()
    c = PolicyCondition(field="x", operator="in", value="a,b,c")
    assert e._match_condition(c, {"x":"b"}) is True

def test_conversation():
    from sam.approval.runtime_v1 import ApprovalRuntimeV1
    assert ApprovalRuntimeV1().conversation_policy.query_count == 10

def test_dashboard():
    from sam.approval.runtime_v1 import ApprovalRuntimeV1
    assert ApprovalRuntimeV1().dashboard_policy.card_count == 3
