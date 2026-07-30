import pytest, os
from dataclasses import FrozenInstanceError
from sam.operations.brain.decision.approval_lifecycle import (
    ApprovalLifecycle, ApprovalLifecycleState, LifecycleTransition,
    LifecycleMetadata, LifecycleStatistics
)
from sam.operations.brain.decision.lifecycle_engine import LifecycleEngine
from sam.operations.brain.decision.lifecycle_rules import LifecycleRules
from sam.operations.brain.decision.lifecycle_history import LifecycleHistory
from sam.operations.brain.decision.lifecycle_validator import LifecycleValidator
from sam.operations.brain.decision.runtime_v3 import DecisionRuntimeV3

# --- DTO frozen ---
def test_approval_lifecycle_frozen():
    l = ApprovalLifecycle(lifecycle_id="l1", session_id="s1", timestamp=0.0)
    with pytest.raises(FrozenInstanceError):
        l.lifecycle_id = "x"

def test_transition_frozen():
    t = LifecycleTransition(from_state="A", to_state="B")
    with pytest.raises(FrozenInstanceError):
        t.from_state = "x"

def test_metadata_frozen():
    m = LifecycleMetadata(lifecycle_id="l1")
    with pytest.raises(FrozenInstanceError):
        m.lifecycle_id = "x"

# --- Rules ---
def test_rules_can_transition():
    assert LifecycleRules.can_transition(ApprovalLifecycleState.CREATED,
                                          ApprovalLifecycleState.VALIDATED)
    assert not LifecycleRules.can_transition(ApprovalLifecycleState.CREATED,
                                              ApprovalLifecycleState.CLOSED)

def test_rules_is_final():
    assert LifecycleRules.is_final(ApprovalLifecycleState.CLOSED)

def test_rules_is_cancellable():
    assert LifecycleRules.is_cancellable(ApprovalLifecycleState.CREATED)

def test_rules_is_active():
    assert LifecycleRules.is_active(ApprovalLifecycleState.READY)

# --- Engine ---
def test_engine_init():
    assert LifecycleEngine() is not None

def test_engine_initialize():
    e = LifecycleEngine()
    l = e.initialize("s1")
    assert l.state == ApprovalLifecycleState.CREATED

def test_engine_transition():
    e = LifecycleEngine()
    l = e.initialize("s1")
    l2 = e.transition(l.lifecycle_id, ApprovalLifecycleState.VALIDATED)
    assert l2 is not None
    assert l2.state == ApprovalLifecycleState.VALIDATED

def test_engine_illegal_transition():
    e = LifecycleEngine()
    l = e.initialize("s1")
    r = e.transition(l.lifecycle_id, ApprovalLifecycleState.CLOSED)
    assert r is None

def test_engine_full_cycle():
    e = LifecycleEngine()
    l = e.initialize("s1")
    l = e.transition(l.lifecycle_id, ApprovalLifecycleState.VALIDATED)
    l = e.transition(l.lifecycle_id, ApprovalLifecycleState.READY)
    l = e.transition(l.lifecycle_id, ApprovalLifecycleState.WAITING)
    l = e.close(l.lifecycle_id)
    assert l.state == ApprovalLifecycleState.CLOSED

def test_engine_cancel():
    e = LifecycleEngine()
    l = e.initialize("s1")
    l = e.cancel(l.lifecycle_id)
    assert l.state == ApprovalLifecycleState.CANCELLED

def test_engine_count():
    e = LifecycleEngine()
    e.initialize("s1")
    e.initialize("s2")
    assert e.count == 2

# --- History ---
def test_history_init():
    assert LifecycleHistory() is not None

def test_history_record():
    h = LifecycleHistory()
    h.record("l1", "created", "NONE", "CREATED")
    assert h.count == 1

def test_history_filter():
    h = LifecycleHistory()
    h.record("l1", "created", "NONE", "CREATED")
    h.record("l2", "created", "NONE", "CREATED")
    assert len(h.filter_by_lifecycle("l1")) == 1

# --- Validator ---
def test_validator_init():
    assert LifecycleValidator() is not None

def test_validator_valid():
    v = LifecycleValidator()
    e = LifecycleEngine()
    l = e.initialize("s1")
    r = v.validate(l)
    assert r.valid is True

def test_validator_invalid():
    v = LifecycleValidator()
    l = ApprovalLifecycle(lifecycle_id="", session_id="", timestamp=0.0)
    r = v.validate(l)
    assert r.valid is False

# --- Runtime integration ---
def test_runtime_lifecycle():
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
    assert st["lifecycle_count"] >= 1

# --- Conversation / Dashboard ---
def test_conversation():
    r = DecisionRuntimeV3()
    assert r.conversation_lifecycle.query_count == 10

def test_dashboard():
    r = DecisionRuntimeV3()
    assert r.dashboard_lifecycle.card_count == 6

# --- Forbidden imports / async ---
def test_forbidden():
    dp = os.path.join("src", "sam", "operations", "brain", "decision")
    fs = ["approval_lifecycle.py","lifecycle_engine.py","lifecycle_rules.py",
          "lifecycle_history.py","lifecycle_validator.py",
          "conversation_lifecycle.py","dashboard_lifecycle.py","runtime_v3.py"]
    for pat in ["import threading","import asyncio","async def","await ","import socket"]:
        for fn in fs:
            p = os.path.join(dp, fn)
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    assert pat not in f.read(), f"{pat} in {fn}"

def test_no_async():
    dp = os.path.join("src", "sam", "operations", "brain", "decision")
    for fn in ["approval_lifecycle.py","lifecycle_engine.py","lifecycle_rules.py",
               "lifecycle_history.py","lifecycle_validator.py",
               "conversation_lifecycle.py","dashboard_lifecycle.py","runtime_v3.py"]:
        p = os.path.join(dp, fn)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                t = f.read()
                assert "async def" not in t
                assert "await " not in t

# --- Deterministic ---
@pytest.mark.parametrize("i", range(100))
def test_deterministic_lifecycle(i):
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
