"""Sprint 257 - Safety Runtime.

Program C - Real Execution Runtime.
Cek: timeout, approval, provider availability, capability, retry limit.
"""
from __future__ import annotations
import pytest

from sam.execution_runtime.execution_request import ExecutionRequest
from sam.execution_runtime.execution_policy import ExecutionPolicy
from sam.execution_runtime.execution_limits import ExecutionLimits
from sam.execution_runtime.execution_rules import ExecutionRules, RuleEvaluation
from sam.execution_runtime.execution_guard import ExecutionGuard, GuardDecision
from sam.execution_runtime.execution_safety import ExecutionSafety, SafetyVerdict


def make_req(mode="preview", approved=False, timeout=60, retries=2, provider="openai", op="chat"):
    return ExecutionRequest(execution_id="e1", provider_id=provider, operation=op,
                            mode=mode, approved=approved, approver="v" if approved else "",
                            timeout_seconds=timeout, max_retries=retries)


def test_policy_defaults():
    p = ExecutionPolicy(policy_id="p1")
    assert p.require_approval is True
    assert p.max_retries == 2
    assert p.max_timeout_seconds == 300


def test_policy_whitelist():
    p = ExecutionPolicy(policy_id="p2", provider_whitelist=("openai", "ollama"))
    assert p.allows_provider("openai") is True
    assert p.allows_provider("gemini") is False
    p2 = ExecutionPolicy(policy_id="p3")
    assert p2.allows_provider("any") is True  # kosong = semua


def test_limits_safe_all_true():
    l = ExecutionLimits(limits_id="l1", execution_id="e1")
    assert l.safe is True
    assert l.as_dict()["safe"] is True


def test_limits_unsafe_if_any_false():
    l = ExecutionLimits(limits_id="l1", execution_id="e1", approved=False)
    assert l.safe is False


def test_rules_all_pass_preview():
    rules = ExecutionRules()
    policy = ExecutionPolicy(policy_id="p1")
    results = rules.evaluate(make_req(mode="preview"), policy)
    assert all(r.passed for r in results)
    assert rules.all_pass(make_req(mode="preview"), policy) is True


def test_rules_timeout_too_high():
    rules = ExecutionRules()
    policy = ExecutionPolicy(policy_id="p1", max_timeout_seconds=100)
    results = rules.evaluate(make_req(timeout=200), policy)
    rule = next(r for r in results if r.rule == "timeout")
    assert rule.passed is False


def test_rules_retry_too_high():
    rules = ExecutionRules()
    policy = ExecutionPolicy(policy_id="p1", max_retries=3)
    results = rules.evaluate(make_req(retries=5), policy)
    rule = next(r for r in results if r.rule == "retry_limit")
    assert rule.passed is False


def test_rules_approval_required_execute():
    rules = ExecutionRules()
    policy = ExecutionPolicy(policy_id="p1")
    results = rules.evaluate(make_req(mode="execute", approved=False), policy)
    rule = next(r for r in results if r.rule == "approval")
    assert rule.passed is False
    assert "approval" in rule.message


def test_rules_approval_ok_execute():
    rules = ExecutionRules()
    policy = ExecutionPolicy(policy_id="p1")
    results = rules.evaluate(make_req(mode="execute", approved=True), policy)
    assert all(r.passed for r in results)


def test_rules_provider_not_allowed():
    rules = ExecutionRules()
    policy = ExecutionPolicy(policy_id="p1", provider_whitelist=("ollama",))
    results = rules.evaluate(make_req(provider="gemini"), policy)
    rule = next(r for r in results if r.rule == "provider_available")
    assert rule.passed is False


def test_rules_capability_missing_operation():
    rules = ExecutionRules()
    policy = ExecutionPolicy(policy_id="p1")
    results = rules.evaluate(make_req(op=""), policy)
    rule = next(r for r in results if r.rule == "capability")
    assert rule.passed is False


def test_guard_allows_safe_execute():
    guard = ExecutionGuard()
    verdict = guard.check("g1", make_req(mode="execute", approved=True))
    assert isinstance(verdict, GuardDecision)
    assert verdict.allowed is True
    assert verdict.limits.safe is True


def test_guard_blocks_unapproved_execute():
    guard = ExecutionGuard()
    verdict = guard.check("g1", make_req(mode="execute", approved=False))
    assert verdict.allowed is False
    assert verdict.limits.approved is False


def test_guard_blocks_timeout_exceed():
    policy = ExecutionPolicy(policy_id="p1", max_timeout_seconds=100)
    guard = ExecutionGuard(policy=policy)
    verdict = guard.check("g1", make_req(mode="preview", timeout=500))
    assert verdict.allowed is False
    assert verdict.limits.within_timeout is False


def test_guard_as_dict():
    guard = ExecutionGuard()
    verdict = guard.check("g1", make_req(mode="preview"))
    d = verdict.as_dict()
    assert d["allowed"] is True
    assert "limits" in d


def test_safety_assess_preview_allowed():
    safety = ExecutionSafety()
    v = safety.assess(make_req(mode="preview"))
    assert isinstance(v, SafetyVerdict)
    assert v.allowed is True
    assert v.external_calls == 0


def test_safety_assess_execute_requires_approval():
    safety = ExecutionSafety()
    v = safety.assess(make_req(mode="execute", approved=False))
    assert v.allowed is False


def test_safety_assess_execute_approved():
    safety = ExecutionSafety()
    v = safety.assess(make_req(mode="execute", approved=True))
    assert v.allowed is True


def test_safety_policy_access():
    safety = ExecutionSafety()
    assert safety.policy.require_approval is True


def test_rule_evaluation_immutable():
    r = RuleEvaluation(rule="timeout", passed=True)
    with pytest.raises(Exception):
        r.passed = False


def test_no_forbidden_imports_safety():
    import inspect
    import sam.execution_runtime.execution_safety as es
    src = inspect.getsource(es)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
