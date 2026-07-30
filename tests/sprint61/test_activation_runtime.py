import pytest, os
from dataclasses import FrozenInstanceError
from sam.operations.brain.decision.approval_activation import *
from sam.operations.brain.decision.approval_lifecycle import *
from sam.operations.brain.decision.activation_engine import ActivationEngine
from sam.operations.brain.decision.activation_rules import ActivationRules
from sam.operations.brain.decision.activation_history import ActivationHistory
from sam.operations.brain.decision.activation_validator import ActivationValidator
from sam.operations.brain.decision.runtime_v3 import DecisionRuntimeV3

# --- DTO frozen ---
def test_activation_frozen():
    a = ApprovalActivation(activation_id="a1", lifecycle_id="l1", session_id="s1", timestamp=0.0)
    with pytest.raises(FrozenInstanceError):
        a.activation_id = "x"

def test_metadata_frozen():
    m = ActivationMetadata(activation_id="a1")
    with pytest.raises(FrozenInstanceError):
        m.activation_id = "x"

# --- Rules ---
def test_rules_readiness():
    lc = ApprovalLifecycle(lifecycle_id="l1", session_id="s1", timestamp=0.0,
                            state=ApprovalLifecycleState.READY, session_ready=True)
    s = ActivationRules.evaluate_readiness(lc)
    assert s >= 0.6

def test_rules_blockers_none():
    lc = ApprovalLifecycle(lifecycle_id="l1", session_id="s1", timestamp=0.0, session_ready=True)
    assert len(ActivationRules.detect_blockers(lc)) == 0

def test_rules_blockers_missing():
    lc = ApprovalLifecycle(lifecycle_id="", session_id="", timestamp=0.0)
    assert len(ActivationRules.detect_blockers(lc)) > 0

# --- Engine ---
def test_engine_init():
    assert ActivationEngine() is not None

def test_engine_evaluate():
    e = ActivationEngine()
    lc = ApprovalLifecycle(lifecycle_id="l1", session_id="s1", timestamp=0.0, session_ready=True)
    a = e.evaluate(lc, "l1", "s1")
    assert a.lifecycle_id == "l1"

def test_engine_statistics():
    e = ActivationEngine()
    lc = ApprovalLifecycle(lifecycle_id="l1", session_id="s1", timestamp=0.0, session_ready=True)
    e.evaluate(lc, "l1", "s1")
    assert e.count == 1
    assert e.get_statistics().total == 1

# --- History ---
def test_history_init():
    assert ActivationHistory() is not None

def test_history_record():
    h = ActivationHistory()
    h.record("a1", "evaluated", "PENDING", "NONE")
    assert h.count == 1

def test_history_filter():
    h = ActivationHistory()
    h.record("a1", "evaluated", "PENDING", "NONE")
    h.record("a2", "blocked", "BLOCKED", "HOLD")
    assert len(h.filter_by_activation("a1")) == 1

# --- Validator ---
def test_validator_init():
    assert ActivationValidator() is not None

def test_validator_valid():
    v = ActivationValidator()
    a = ApprovalActivation(activation_id="a1", lifecycle_id="l1", session_id="s1", timestamp=0.0)
    r = v.validate(a)
    assert r.valid is True

def test_validator_invalid():
    v = ActivationValidator()
    a = ApprovalActivation(activation_id="", lifecycle_id="", session_id="", timestamp=0.0)
    r = v.validate(a)
    assert r.valid is False

# --- Runtime integration ---
def test_runtime_activation():
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
    assert st["activation_count"] >= 1

# --- Conversation / Dashboard ---
def test_conversation():
    r = DecisionRuntimeV3()
    assert r.conversation_activation.query_count == 10

def test_dashboard():
    r = DecisionRuntimeV3()
    assert r.dashboard_activation.card_count == 6

# --- Forbidden ---
def test_forbidden():
    dp = os.path.join("src", "sam", "operations", "brain", "decision")
    fs = ["approval_activation.py","activation_engine.py","activation_rules.py",
          "activation_history.py","activation_validator.py",
          "conversation_activation.py","dashboard_activation.py","runtime_v3.py"]
    for pat in ["import threading","import asyncio","async def","await ","import socket"]:
        for fn in fs:
            p = os.path.join(dp, fn)
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    assert pat not in f.read(), f"{pat} in {fn}"

def test_no_async():
    dp = os.path.join("src", "sam", "operations", "brain", "decision")
    for fn in ["approval_activation.py","activation_engine.py","activation_rules.py",
               "activation_history.py","activation_validator.py",
               "conversation_activation.py","dashboard_activation.py","runtime_v3.py"]:
        p = os.path.join(dp, fn)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                t = f.read()
                assert "async def" not in t
                assert "await " not in t

# --- Deterministic ---
@pytest.mark.parametrize("i", range(100))
def test_deterministic_activation(i):
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
