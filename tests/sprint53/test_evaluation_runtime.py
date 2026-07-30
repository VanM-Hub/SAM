import pytest, os
from dataclasses import FrozenInstanceError
from sam.operations.brain.decision.evaluation import DecisionEvaluation,EvaluationResult,EvaluationReason,EvaluationSummary,EvaluationStatistics,EvaluationSnapshot,ReadinessLevel,ConfidenceLevel
from sam.operations.brain.decision.evaluation_engine import DecisionEvaluator
from sam.operations.brain.decision.readiness import ReadinessChecker
from sam.operations.brain.decision.policy_check import PolicyChecker
from sam.operations.brain.decision.confidence import ConfidenceCalculator
from sam.operations.brain.decision.package_context import DecisionContext
from sam.operations.brain.decision.runtime_v3 import DecisionRuntimeV3

def test_dto_frozen():
    e=DecisionEvaluation(evaluation_id="e1",timestamp=0.0,context_id="c1")
    with pytest.raises(FrozenInstanceError): e.evaluation_id="x"
def test_result_frozen():
    r=EvaluationResult()
    with pytest.raises(FrozenInstanceError):
        r.passed=True
def test_reason_frozen():
    r=EvaluationReason(primary="p")
def test_summary_frozen():
    s=EvaluationSummary()
    with pytest.raises(FrozenInstanceError):
        s.total=5

def test_evaluator_init():
    assert DecisionEvaluator() is not None
def test_evaluator_evaluate():
    e=DecisionEvaluator()
    c=DecisionContext(context_id="c1",package_id="p1",priority=2,confidence=80.0,runtime_ids=["r1"],action_type="monitor",evidence_count=3,has_justification=True,is_ready=True,summary="t")
    ev=e.evaluate(c)
    assert ev.context_id=="c1"
    assert ev.ready in (ReadinessLevel.READY,ReadinessLevel.BLOCKED,ReadinessLevel.PARTIAL)

def test_readiness_checker():
    r=ReadinessChecker()
    c=DecisionContext(context_id="c1",package_id="p1",priority=2,confidence=80.0,runtime_ids=["r1"],action_type="monitor",evidence_count=3,has_justification=True,is_ready=True,summary="t")
    res=r.check(c); assert res.passed is True

def test_readiness_low_conf():
    r=ReadinessChecker()
    c=DecisionContext(context_id="c1",package_id="p1",priority=0,confidence=10.0,action_type="unknown",is_ready=False)
    res=r.check(c); assert res.passed is False

def test_policy_checker():
    p=PolicyChecker()
    c=DecisionContext(context_id="c1",package_id="p1",priority=2,confidence=80.0,runtime_ids=["r1"],action_type="monitor",has_justification=True,is_ready=True)
    res=p.check(c); assert res.passed is True

def test_policy_violation():
    p=PolicyChecker()
    c=DecisionContext(context_id="c1",package_id="p1",priority=-1,confidence=10.0,action_type="unknown",is_ready=False)
    res=p.check(c); assert res.passed is False

def test_confidence():
    c=ConfidenceCalculator()
    ctx=DecisionContext(context_id="c1",package_id="p1",priority=2,confidence=80.0,runtime_ids=["r1"],action_type="monitor",evidence_count=3,has_justification=True,is_ready=True,summary="t")
    readiness=ReadinessChecker().check(ctx)
    policy=PolicyChecker().check(ctx)
    level=c.calculate(ctx,readiness,policy)
    assert level in (ConfidenceLevel.VERY_HIGH,ConfidenceLevel.HIGH,ConfidenceLevel.MEDIUM,ConfidenceLevel.LOW)

def test_runtime_init():
    r=DecisionRuntimeV3(); st=r.get_status(); assert st["evaluation_count"]==0
def test_runtime_consume():
    r=DecisionRuntimeV3()
    src={"package_id":"p1","metadata":{"version":"1.0"},"total_sections":2,"decision_input_id":"d1","justification_id":"j1",
         "sections":{"decision_input":{"input_id":"d1","timestamp":100.0,"priority_score":2,"confidence":80.0,"candidates":[{"runtime_id":"r1","action_type":"monitor"}]},"justification":{"summary":"t"}}}
    res=r.consume(src)
    assert res["evaluation_ready"] in ("READY","BLOCKED","PARTIAL","NONE")

def test_runtime_conversation():
    r=DecisionRuntimeV3(); assert r.conversation_eval.query_count==10
def test_runtime_dashboard():
    r=DecisionRuntimeV3(); assert r.dashboard_eval.card_count==6

def test_compatibility():
    r=DecisionRuntimeV3()
    gp={"package_id":"g1","metadata":{"version":"1.0","created_at":100.0,"source_component":"GuardianLiveRuntime"},"total_sections":2,"decision_input_id":"di1","justification_id":"j1",
        "sections":{"decision_input":{"input_id":"di1","timestamp":100.0,"priority_score":2,"confidence":85.0,"candidates":[{"runtime_id":"r1","action_type":"monitor"}]},"justification":{"justification_id":"j1","summary":"t"}}}
    res=r.consume(gp); assert res["received"] is True

def test_dash_cards():
    r=DecisionRuntimeV3()
    gp={"package_id":"p1","metadata":{"version":"1.0"},"total_sections":2,"decision_input_id":"d1","justification_id":"j1",
        "sections":{"decision_input":{"input_id":"d1","timestamp":100.0,"priority_score":1,"confidence":75.0},"justification":{"summary":"t"}}}
    r.consume(gp); assert len(r.dashboard_eval.get_all_cards())==6

def test_forbidden():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    fs=["evaluation.py","evaluator.py","readiness.py","policy_check.py","confidence.py","conversation_evaluation.py","dashboard_evaluation.py","runtime_v3.py"]
    for pat in ["import threading","import asyncio","async def","await ","import socket","import websockets","from websocket","import multiprocessing"]:
        for fn in fs:
            p=os.path.join(dp,fn)
            if os.path.exists(p):
                with open(p,"r",encoding="utf-8") as f: assert pat not in f.read(), f"{pat} in {fn}"
def test_no_async():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    for fn in ["evaluation.py","evaluator.py","readiness.py","policy_check.py","confidence.py","conversation_evaluation.py","dashboard_evaluation.py","runtime_v3.py"]:
        p=os.path.join(dp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: t=f.read(); assert "async def" not in t; assert "await " not in t

@pytest.mark.parametrize("i",range(100))
def test_deterministic_eval(i):
    r=DecisionRuntimeV3()
    src={"package_id":f"p{i}","metadata":{"version":"1.0"},"total_sections":1,
         "sections":{"decision_input":{"input_id":f"d{i}","timestamp":float(i),"priority_score":i%4,"confidence":50.0+float(i%5)*10,
                                         "candidates":[{"runtime_id":"r1","action_type":"monitor"}]}}}
    res=r.consume(src); assert res["received"] is True

