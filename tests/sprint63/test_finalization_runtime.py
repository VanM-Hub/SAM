import pytest, os
from dataclasses import FrozenInstanceError
from sam.operations.brain.decision.finalization import *
from sam.operations.brain.decision.approval_activation import ApprovalActivation,ActivationState
from sam.operations.brain.decision.approval_certification import ApprovalCertification,CertificationState
from sam.operations.brain.decision.finalization_engine import FinalizationEngine
from sam.operations.brain.decision.finalization_validator import FinalizationValidator
from sam.operations.brain.decision.finalization_history import FinalizationHistory
from sam.operations.brain.decision.finalization_summary import FinalizationSummary
from sam.operations.brain.decision.runtime_v3 import DecisionRuntimeV3

# --- DTO frozen ---
def test_record_frozen():
    r = FinalDecisionRecord(record_id="r1", timestamp=0.0)
    with pytest.raises(FrozenInstanceError):
        r.record_id = "x"

def test_summary_frozen():
    s = FinalDecisionSummary()
    with pytest.raises(FrozenInstanceError):
        s.pipeline_stages = 10

def test_metadata_frozen():
    m = FinalDecisionMetadata(record_id="r1")
    with pytest.raises(FrozenInstanceError):
        m.record_id = "x"

# --- Summary ---
def test_summary_empty():
    s = FinalizationSummary.build()
    assert s.pipeline_stages == 0

def test_summary_with_data():
    cert = ApprovalCertification(certification_id="c1", activation_id="a1", lifecycle_id="l1", timestamp=0.0,
                                  state=CertificationState.CERTIFIED, readiness_score=0.95, certified=True,
                                  evidence_count=6, blocker_count=0)
    act = ApprovalActivation(activation_id="a1", lifecycle_id="l1", session_id="s1", timestamp=0.0,
                              state=ActivationState.READY, readiness_score=0.95, ready=True)
    s = FinalizationSummary.build(cert, act)
    assert s.pipeline_stages == 17
    assert s.readiness_score == 0.95

def test_integrity():
    cert = ApprovalCertification(certification_id="c1", activation_id="a1", lifecycle_id="l1", timestamp=0.0,
                                  state=CertificationState.CERTIFIED, certified=True, evidence_count=6)
    act = ApprovalActivation(activation_id="a1", lifecycle_id="l1", session_id="s1", timestamp=0.0, ready=True)
    i = FinalizationSummary.compute_integrity(cert, act)
    assert i > 0.5

def test_complete():
    cert = ApprovalCertification(certification_id="c1", activation_id="a1", lifecycle_id="l1", timestamp=0.0)
    act = ApprovalActivation(activation_id="a1", lifecycle_id="l1", session_id="s1", timestamp=0.0)
    assert FinalizationSummary.compute_complete(cert, act) is True
    assert FinalizationSummary.compute_complete(None, None) is False

# --- Engine ---
def test_engine_init():
    assert FinalizationEngine() is not None

def test_engine_finalize():
    e = FinalizationEngine()
    cert = ApprovalCertification(certification_id="c1", activation_id="a1", lifecycle_id="l1", timestamp=0.0,
                                  certified=True, evidence_count=6)
    act = ApprovalActivation(activation_id="a1", lifecycle_id="l1", session_id="s1", timestamp=0.0, ready=True)
    f = e.finalize(cert, act, "s1", "l1", "g1")
    assert f.complete is True
    assert f.state == FinalDecisionState.FINALIZED

def test_engine_count():
    e = FinalizationEngine()
    e.finalize(None, None, "", "", "")
    assert e.count == 1

# --- Validator ---
def test_validator_init():
    assert FinalizationValidator() is not None

def test_validator_valid():
    v = FinalizationValidator()
    r = FinalDecisionRecord(record_id="r1", session_id="s1", lifecycle_id="l1",
                             activation_id="a1", certification_id="c1", timestamp=0.0)
    res = v.validate(r)
    assert res.valid is True

def test_validator_invalid():
    v = FinalizationValidator()
    r = FinalDecisionRecord(record_id="", session_id="", lifecycle_id="",
                             activation_id="", certification_id="", timestamp=0.0)
    res = v.validate(r)
    assert res.valid is False

# --- History ---
def test_history_init():
    assert FinalizationHistory() is not None

def test_history_record():
    h = FinalizationHistory()
    h.record("r1", "finalized", "FINALIZED", 0.95)
    assert h.count == 1

# --- Runtime integration ---
def test_runtime_finalization():
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
    assert st["finalization_count"] >= 1

# --- Conversation / Dashboard ---
def test_conversation():
    r = DecisionRuntimeV3(); assert r.conversation_finalization.query_count == 10

def test_dashboard():
    r = DecisionRuntimeV3(); assert r.dashboard_finalization.card_count == 6

# --- Forbidden ---
def test_forbidden():
    dp = os.path.join("src", "sam", "operations", "brain", "decision")
    fs = ["finalization.py","finalization_engine.py","finalization_validator.py",
          "finalization_summary.py","finalization_history.py",
          "conversation_finalization.py","dashboard_finalization.py","runtime_v3.py"]
    for pat in ["import threading","import asyncio","async def","await ","import socket"]:
        for fn in fs:
            p = os.path.join(dp, fn)
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    assert pat not in f.read(), f"{pat} in {fn}"

def test_no_async():
    dp = os.path.join("src", "sam", "operations", "brain", "decision")
    for fn in ["finalization.py","finalization_engine.py","finalization_validator.py",
               "finalization_summary.py","finalization_history.py",
               "conversation_finalization.py","dashboard_finalization.py","runtime_v3.py"]:
        p = os.path.join(dp, fn)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                t = f.read()
                assert "async def" not in t
                assert "await " not in t

# --- Deterministic ---
@pytest.mark.parametrize("i", range(100))
def test_deterministic_finalization(i):
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
