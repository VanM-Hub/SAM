import pytest, os
from dataclasses import FrozenInstanceError
from sam.operations.brain.decision.submission_plan import ApprovalSubmissionPlan,SubmissionStage,SubmissionReference,SubmissionMetadata,SubmissionStatistics,SubmissionSnapshot
from sam.operations.brain.decision.submission_builder import SubmissionBuilder
from sam.operations.brain.decision.submission_validator import SubmissionValidator
from sam.operations.brain.decision.submission_queue import SubmissionQueuePlanner,SubmissionQueue
from sam.operations.brain.decision.submission_summary import SubmissionSummaryBuilder
from sam.operations.brain.decision.approval_envelope import ApprovalRequestEnvelope,ApprovalReference,ApprovalPayload
from sam.operations.brain.decision.runtime_v3 import DecisionRuntimeV3

def test_dto_frozen():
    p=ApprovalSubmissionPlan(plan_id="p1",timestamp=0.0,envelope_id="e1")
    with pytest.raises(FrozenInstanceError): p.plan_id="x"
def test_stage_frozen():
    s=SubmissionStage(name="s")
    with pytest.raises(FrozenInstanceError):
        s.name="x"
def test_meta_frozen():
    m=SubmissionMetadata(submission_id="s1")
    with pytest.raises(FrozenInstanceError):
        m.submission_id="x"

def test_builder_init():
    assert SubmissionBuilder() is not None
def test_builder_build():
    b=SubmissionBuilder()
    e=ApprovalRequestEnvelope(envelope_id="e1",timestamp=0.0,payload=ApprovalPayload(action_type="monitor"),ready=True)
    p=b.build(e); assert p.envelope_id=="e1"; assert p.ready is True

def test_validator_init():
    assert SubmissionValidator() is not None
def test_validator_valid():
    v=SubmissionValidator()
    e=ApprovalRequestEnvelope(envelope_id="e1",timestamp=0.0,payload=ApprovalPayload(action_type="monitor"),ready=True)
    p=SubmissionBuilder().build(e); r=v.validate(p); assert r.valid is True

def test_queue_init():
    assert SubmissionQueuePlanner() is not None
def test_queue_plan():
    q=SubmissionQueuePlanner()
    e=ApprovalRequestEnvelope(envelope_id="e1",timestamp=0.0,payload=ApprovalPayload(action_type="monitor"),ready=True)
    p=SubmissionBuilder().build(e)
    qq=q.plan([p]); assert qq.total>=1

def test_summary_init():
    assert SubmissionSummaryBuilder() is not None
def test_summary_build():
    s=SubmissionSummaryBuilder()
    e=ApprovalRequestEnvelope(envelope_id="e1",timestamp=0.0,payload=ApprovalPayload(action_type="monitor"),ready=True)
    p=SubmissionBuilder().build(e); sm=s.build(p); assert "plan_id" in sm

def test_runtime_init():
    r=DecisionRuntimeV3(); st=r.get_status(); assert "submission_count" in st
def test_runtime_submission():
    r=DecisionRuntimeV3()
    src={"package_id":"p1","metadata":{"version":"1.0"},"total_sections":2,"decision_input_id":"d1","justification_id":"j1",
         "sections":{"decision_input":{"input_id":"d1","timestamp":100.0,"priority_score":2,"confidence":80.0,"candidates":[{"runtime_id":"r1","action_type":"monitor"}]},"justification":{"summary":"t"}}}
    res=r.consume(src); st=r.get_status(); assert st["submission_count"]>=1

def test_conversation():
    r=DecisionRuntimeV3(); assert r.conversation_submission.query_count==10
def test_dashboard():
    r=DecisionRuntimeV3(); assert r.dashboard_submission.card_count==6

def test_forbidden():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    fs=["submission_plan.py","submission_builder.py","submission_validator.py","submission_queue.py","submission_summary.py","conversation_submission.py","dashboard_submission.py","runtime_v3.py"]
    for pat in ["import threading","import asyncio","async def","await ","import socket"]:
        for fn in fs:
            p=os.path.join(dp,fn); 
            if os.path.exists(p):
                with open(p,"r",encoding="utf-8") as f: assert pat not in f.read(), f"{pat} in {fn}"
def test_no_async():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    for fn in ["submission_plan.py","submission_builder.py","submission_validator.py","submission_queue.py","submission_summary.py","conversation_submission.py","dashboard_submission.py","runtime_v3.py"]:
        p=os.path.join(dp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: t=f.read(); assert "async def" not in t; assert "await " not in t

@pytest.mark.parametrize("i",range(100))
def test_deterministic_submission(i):
    r=DecisionRuntimeV3()
    src={"package_id":f"p{i}","metadata":{"version":"1.0"},"total_sections":1,
         "sections":{"decision_input":{"input_id":f"d{i}","timestamp":float(i),"priority_score":i%4,"confidence":50.0+float(i%5)*10,
                                         "candidates":[{"runtime_id":"r1","action_type":"monitor"}]}}}
    res=r.consume(src); assert res["received"] is True

