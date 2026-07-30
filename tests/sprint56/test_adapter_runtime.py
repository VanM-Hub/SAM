import pytest, os
from dataclasses import FrozenInstanceError
from sam.operations.brain.decision.approval_envelope import ApprovalRequestEnvelope,ApprovalReference,ApprovalPayload,ApprovalEnvelopeStatistics,ApprovalEnvelopeSnapshot
from sam.operations.brain.decision.approval_mapper import ApprovalMapper
from sam.operations.brain.decision.approval_adapter import ApprovalAdapter
from sam.operations.brain.decision.approval_bridge import ApprovalBridge
from sam.operations.brain.decision.approval_status import ApprovalStatusMirrorStore,ApprovalStatusMirror,ApprovalState,ApprovalStateSummary,ApprovalStateStatistics
from sam.operations.brain.decision.approval_preparation import ApprovalPreparation,ApprovalMetadata,ApprovalCandidate
from sam.operations.brain.decision.approval_builder import ApprovalBuilder
from sam.operations.brain.decision.evaluation import DecisionEvaluation,EvaluationResult,ReadinessLevel,ConfidenceLevel
from sam.operations.brain.decision.planner import DecisionPlanner
from sam.operations.brain.decision.runtime_v3 import DecisionRuntimeV3

def test_dto_frozen():
    e=ApprovalRequestEnvelope(envelope_id="e1",timestamp=0.0)
    with pytest.raises(FrozenInstanceError): e.envelope_id="x"
def test_ref_frozen():
    r=ApprovalReference()
    with pytest.raises(FrozenInstanceError): r.preparation_id="x"
def test_payload_frozen():
    p=ApprovalPayload()
    with pytest.raises(FrozenInstanceError): p.action_type="x"

def test_mapper_init():
    assert ApprovalMapper() is not None
def test_mapper_map():
    m=ApprovalMapper()
    a=ApprovalPreparation(preparation_id="p1",timestamp=0.0,
        metadata=ApprovalMetadata(plan_id="pl1",evaluation_id="ev1"),
        candidates=[ApprovalCandidate(candidate_id="c1",runtime_id="r1",action_type="monitor",priority=2,confidence=80.0)],
        ready_for_submission=True)
    e=m.map(a)
    assert e.references.plan_id=="pl1"
    assert e.payload.action_type=="monitor"

def test_adapter_init():
    assert ApprovalAdapter() is not None
def test_adapter_valid():
    a=ApprovalAdapter()
    e=ApprovalRequestEnvelope(envelope_id="e1",timestamp=0.0,
        references=ApprovalReference(preparation_id="p1",plan_id="pl1"),
        payload=ApprovalPayload(action_type="monitor",priority=2,confidence=80.0,requires_approval=True),
        ready=True)
    r=a.process(e); assert r.success is True

def test_bridge_init():
    assert ApprovalBridge() is not None
def test_bridge_process():
    b=ApprovalBridge()
    a=ApprovalPreparation(preparation_id="p1",timestamp=0.0,
        metadata=ApprovalMetadata(plan_id="pl1",evaluation_id="ev1"),
        candidates=[ApprovalCandidate(candidate_id="c1",runtime_id="r1",action_type="monitor",priority=2,confidence=80.0)],
        ready_for_submission=True)
    r=b.bridge(a); assert r["mapped"] is True
    assert b.bridge_count==1

def test_status_init():
    s=ApprovalStatusMirrorStore(); assert s.latest.state=="PENDING"
def test_status_record():
    s=ApprovalStatusMirrorStore()
    m=ApprovalStatusMirror(envelope_id="e1",state=ApprovalState.PENDING,timestamp=0.0)
    s.record(m); assert s.latest.envelope_id=="e1"

def test_runtime_adapter():
    r=DecisionRuntimeV3()
    src={"package_id":"p1","metadata":{"version":"1.0"},"total_sections":2,"decision_input_id":"d1","justification_id":"j1",
         "sections":{"decision_input":{"input_id":"d1","timestamp":100.0,"priority_score":2,"confidence":80.0,"candidates":[{"runtime_id":"r1","action_type":"monitor"}]},"justification":{"summary":"t"}}}
    res=r.consume(src); st=r.get_status(); assert st["bridge_count"]>=1

def test_conversation():
    r=DecisionRuntimeV3(); assert r.conversation_adapter.query_count==10
def test_dashboard():
    r=DecisionRuntimeV3(); assert r.dashboard_adapter.card_count==6

def test_forbidden():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    fs=["approval_envelope.py","approval_mapper.py","approval_adapter.py","approval_bridge.py","approval_status.py","conversation_adapter.py","dashboard_adapter.py","runtime_v3.py"]
    for pat in ["import threading","import asyncio","async def","await ","import socket"]:
        for fn in fs:
            p=os.path.join(dp,fn)
            if os.path.exists(p):
                with open(p,"r",encoding="utf-8") as f: assert pat not in f.read(), f"{pat} in {fn}"
def test_no_async():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    for fn in ["approval_envelope.py","approval_mapper.py","approval_adapter.py","approval_bridge.py","approval_status.py","conversation_adapter.py","dashboard_adapter.py","runtime_v3.py"]:
        p=os.path.join(dp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: t=f.read(); assert "async def" not in t; assert "await " not in t

@pytest.mark.parametrize("i",range(100))
def test_deterministic_adapter(i):
    r=DecisionRuntimeV3()
    src={"package_id":f"p{i}","metadata":{"version":"1.0"},"total_sections":1,
         "sections":{"decision_input":{"input_id":f"d{i}","timestamp":float(i),"priority_score":i%4,"confidence":50.0+float(i%5)*10,
                                         "candidates":[{"runtime_id":"r1","action_type":"monitor"}]}}}
    res=r.consume(src); assert res["received"] is True
