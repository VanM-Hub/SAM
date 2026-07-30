import pytest, os
from dataclasses import FrozenInstanceError
from sam.operations.brain.decision.approval_certification import *
from sam.operations.brain.decision.approval_activation import ApprovalActivation, ActivationState, ActivationDecision
from sam.operations.brain.decision.certification_engine import CertificationEngine
from sam.operations.brain.decision.certification_rules import CertificationRules
from sam.operations.brain.decision.certification_history import CertificationHistory
from sam.operations.brain.decision.certification_validator import CertificationValidator
from sam.operations.brain.decision.runtime_v3 import DecisionRuntimeV3

# --- DTO frozen ---
def test_certification_frozen():
    c = ApprovalCertification(certification_id="c1", activation_id="a1", lifecycle_id="l1", timestamp=0.0)
    with pytest.raises(FrozenInstanceError):
        c.certification_id = "x"

def test_requirement_frozen():
    r = CertificationRequirement(name="test", met=True)
    with pytest.raises(FrozenInstanceError):
        r.name = "x"

# --- Rules ---
def test_rules_requirements_full():
    a = ApprovalActivation(activation_id="a1", lifecycle_id="l1", session_id="s1", timestamp=0.0,
                           state=ActivationState.READY, readiness_score=0.9, blockers=[])
    reqs, all_met = CertificationRules.evaluate_requirements(a)
    assert all_met is True
    assert len(reqs) == 7

def test_rules_requirements_missing():
    a = ApprovalActivation(activation_id="", lifecycle_id="", session_id="", timestamp=0.0)
    reqs, all_met = CertificationRules.evaluate_requirements(a)
    assert all_met is False

def test_rules_state():
    assert CertificationRules.determine_state(0.95, 0, True) == "CERTIFIED"
    assert CertificationRules.determine_state(0.7, 0, True) == "CONDITIONALLY_READY"
    assert CertificationRules.determine_state(0.5, 1, True) == "BLOCKED"
    assert CertificationRules.determine_state(0.3, 0, False) == "FAILED"

def test_rules_decision():
    assert CertificationRules.determine_decision("CERTIFIED") == "APPROVE"
    assert CertificationRules.determine_decision("CONDITIONALLY_READY") == "CONDITIONAL"
    assert CertificationRules.determine_decision("BLOCKED") == "REJECT"

# --- Engine ---
def test_engine_init():
    assert CertificationEngine() is not None

def test_engine_certify():
    e = CertificationEngine()
    a = ApprovalActivation(activation_id="a1", lifecycle_id="l1", session_id="s1", timestamp=0.0,
                           state=ActivationState.READY, readiness_score=0.9, blockers=[])
    c = e.certify(a, "a1", "l1")
    assert c.certified is True

def test_engine_reject():
    e = CertificationEngine()
    a = ApprovalActivation(activation_id="", lifecycle_id="", session_id="", timestamp=0.0)
    c = e.certify(a, "a1", "l1")
    assert c.certified is False

def test_engine_statistics():
    e = CertificationEngine()
    a = ApprovalActivation(activation_id="a1", lifecycle_id="l1", session_id="s1", timestamp=0.0,
                           readiness_score=0.9, blockers=[])
    e.certify(a, "a1", "l1")
    assert e.count == 1

# --- History ---
def test_history_init():
    assert CertificationHistory() is not None

def test_history_record():
    h = CertificationHistory()
    h.record("c1", "certified", "CERTIFIED", "APPROVE")
    assert h.count == 1

# --- Validator ---
def test_validator_init():
    assert CertificationValidator() is not None

def test_validator_valid():
    v = CertificationValidator()
    c = ApprovalCertification(certification_id="c1", activation_id="a1", lifecycle_id="l1", timestamp=0.0)
    r = v.validate(c)
    assert r.valid is True

def test_validator_invalid():
    v = CertificationValidator()
    c = ApprovalCertification(certification_id="", activation_id="", lifecycle_id="", timestamp=0.0)
    r = v.validate(c)
    assert r.valid is False

# --- Runtime integration ---
def test_runtime_certification():
    r = DecisionRuntimeV3()
    src = {"package_id":"p1","metadata":{"version":"1.0"},"total_sections":2,
           "decision_input_id":"d1","justification_id":"j1",
           "sections":{
               "decision_input":{"input_id":"d1","timestamp":100.0,"priority_score":2,
                                  "confidence":80.0,
                                  "candidates":[{"runtime_id":"r1","action_type":"monitor"}]},
               "justification":{"summary":"t"}
           }}
    res = r.consume(src)
    st = r.get_status()
    assert st["certification_count"] >= 1

# --- Conversation / Dashboard ---
def test_conversation():
    r = DecisionRuntimeV3(); assert r.conversation_certification.query_count == 10

def test_dashboard():
    r = DecisionRuntimeV3(); assert r.dashboard_certification.card_count == 6

# --- Forbidden ---
def test_forbidden():
    dp = os.path.join("src", "sam", "operations", "brain", "decision")
    fs = ["approval_certification.py","certification_engine.py","certification_rules.py",
          "certification_history.py","certification_validator.py",
          "conversation_certification.py","dashboard_certification.py","runtime_v3.py"]
    for pat in ["import threading","import asyncio","async def","await ","import socket"]:
        for fn in fs:
            p = os.path.join(dp, fn)
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    assert pat not in f.read(), f"{pat} in {fn}"

def test_no_async():
    dp = os.path.join("src", "sam", "operations", "brain", "decision")
    for fn in ["approval_certification.py","certification_engine.py","certification_rules.py",
               "certification_history.py","certification_validator.py",
               "conversation_certification.py","dashboard_certification.py","runtime_v3.py"]:
        p = os.path.join(dp, fn)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                t = f.read()
                assert "async def" not in t
                assert "await " not in t

# --- Deterministic ---
@pytest.mark.parametrize("i", range(100))
def test_deterministic_certification(i):
    r = DecisionRuntimeV3()
    src = {"package_id": f"p{i}", "metadata": {"version": "1.0"}, "total_sections": 1,
           "sections": {
               "decision_input": {"input_id": f"d{i}", "timestamp": float(i),
                                   "priority_score": i % 4,
                                   "confidence": 50.0 + float(i % 5) * 10,
                                   "candidates": [{"runtime_id": "r1", "action_type": "monitor"}]}
           }}
    res = r.consume(src)
    assert res["received"] is True
