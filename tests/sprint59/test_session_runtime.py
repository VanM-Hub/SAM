import pytest, os
from dataclasses import FrozenInstanceError
from sam.operations.brain.decision.approval_session import ApprovalSession,ApprovalSessionState,ApprovalSessionReference,ApprovalSessionMetadata
from sam.operations.brain.decision.session_builder import SessionBuilder
from sam.operations.brain.decision.session_validator import SessionValidator
from sam.operations.brain.decision.session_registry import SessionRegistry
from sam.operations.brain.decision.session_history import SessionHistory,SessionHistoryRecord
from sam.operations.brain.decision.gateway_request import ApprovalGatewayRequest,GatewayReference,GatewayMetadata
from sam.operations.brain.decision.runtime_v3 import DecisionRuntimeV3

def test_dto_frozen():
    s=ApprovalSession(session_id="s1",timestamp=0.0)
    with pytest.raises(FrozenInstanceError): s.session_id="x"
def test_ref_frozen():
    r=ApprovalSessionReference()
    with pytest.raises(FrozenInstanceError):
        r.gateway_request_id="x"
def test_meta_frozen():
    m=ApprovalSessionMetadata(session_id="s1")
    with pytest.raises(FrozenInstanceError):
        m.session_id="x"

def test_builder_init():
    assert SessionBuilder() is not None
def test_builder_build():
    b=SessionBuilder()
    r=ApprovalGatewayRequest(request_id="r1",timestamp=0.0,references=GatewayReference(submission_plan_id="sp1"),ready=True)
    s=b.build(r); assert s.references.gateway_request_id=="r1"; assert s.ready is True

def test_validator_init():
    assert SessionValidator() is not None
def test_validator_valid():
    v=SessionValidator()
    b=SessionBuilder()
    s=b.build(ApprovalGatewayRequest(request_id="r1",timestamp=0.0,ready=True))
    r=v.validate(s); assert r.valid is True

def test_registry_init():
    assert SessionRegistry() is not None
def test_registry_count():
    r=SessionRegistry()
    s=ApprovalSession(session_id="s1",timestamp=0.0)
    r.register(s); assert r.count==1
def test_registry_lookup():
    r=SessionRegistry()
    s=ApprovalSession(session_id="find-me",timestamp=0.0)
    r.register(s); assert r.lookup("find-me") is not None

def test_history_init():
    assert SessionHistory() is not None
def test_history_record():
    h=SessionHistory()
    h.record("s1","created","NONE","CREATED"); assert h.count==1
def test_history_filter():
    h=SessionHistory()
    h.record("s1","created","NONE","CREATED"); h.record("s2","created","NONE","CREATED")
    assert len(h.filter_by_session("s1"))==1

def test_runtime_session():
    r=DecisionRuntimeV3()
    src={"package_id":"p1","metadata":{"version":"1.0"},"total_sections":2,"decision_input_id":"d1","justification_id":"j1",
         "sections":{"decision_input":{"input_id":"d1","timestamp":100.0,"priority_score":2,"confidence":80.0,"candidates":[{"runtime_id":"r1","action_type":"monitor"}]},"justification":{"summary":"t"}}}
    res=r.consume(src); st=r.get_status(); assert st["session_count"]>=1

def test_conversation():
    r=DecisionRuntimeV3(); assert r.conversation_session.query_count==10
def test_dashboard():
    r=DecisionRuntimeV3(); assert r.dashboard_session.card_count==6

def test_forbidden():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    fs=["approval_session.py","session_builder.py","session_validator.py","session_registry.py","session_history.py","conversation_session.py","dashboard_session.py","runtime_v3.py"]
    for fn in fs:
        p=os.path.join(dp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: t=f.read()
            for pat in ["import threading","import asyncio","async def","await ","import socket"]: assert pat not in t
def test_no_async():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    for fn in ["approval_session.py","session_builder.py","session_validator.py","session_registry.py","session_history.py","conversation_session.py","dashboard_session.py","runtime_v3.py"]:
        p=os.path.join(dp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: t=f.read(); assert "async def" not in t; assert "await " not in t

@pytest.mark.parametrize("i",range(100))
def test_deterministic_session(i):
    r=DecisionRuntimeV3()
    src={"package_id":f"p{i}","metadata":{"version":"1.0"},"total_sections":1,
         "sections":{"decision_input":{"input_id":f"d{i}","timestamp":float(i),"priority_score":i%4,"confidence":50.0+float(i%5)*10,
                                         "candidates":[{"runtime_id":"r1","action_type":"monitor"}]}}}
    res=r.consume(src); assert res["received"] is True

