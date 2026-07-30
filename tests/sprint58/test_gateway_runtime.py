import pytest, os, uuid
from dataclasses import FrozenInstanceError
from sam.operations.brain.decision.gateway_request import ApprovalGatewayRequest,GatewayReference,GatewayMetadata,GatewayStatistics,GatewaySnapshot
from sam.operations.brain.decision.approval_gateway import ApprovalGateway,ApprovalGatewayResult
from sam.operations.brain.decision.gateway_router import GatewayRouter
from sam.operations.brain.decision.gateway_validator import GatewayValidator
from sam.operations.brain.decision.gateway_registry import GatewayRegistry
from sam.operations.brain.decision.submission_plan import ApprovalSubmissionPlan,SubmissionMetadata,SubmissionStage
from sam.operations.brain.decision.runtime_v3 import DecisionRuntimeV3

def test_dto_frozen():
    r=ApprovalGatewayRequest(request_id="r1",timestamp=0.0)
    with pytest.raises(FrozenInstanceError): r.request_id="x"
def test_ref_frozen():
    r=GatewayReference()
    with pytest.raises(FrozenInstanceError): r.submission_plan_id="x"
def test_meta_frozen():
    m=GatewayMetadata(gateway_id="g1")
    with pytest.raises(FrozenInstanceError): m.gateway_id="x"

def test_router_init():
    assert GatewayRouter() is not None
def test_router_default():
    r=GatewayRouter()
    p=ApprovalSubmissionPlan(plan_id="p1",timestamp=0.0,envelope_id="e1")
    route=r.route(p); assert route=="manual"  # not ready
def test_router_fast_track():
    r=GatewayRouter()
    p=ApprovalSubmissionPlan(plan_id="p1",timestamp=0.0,envelope_id="e1",ready=True,metadata=SubmissionMetadata(submission_id="s1",priority=3))
    route=r.route(p); assert route=="fast_track"

def test_validator_init():
    assert GatewayValidator() is not None
def test_validator_valid():
    v=GatewayValidator()
    p=ApprovalSubmissionPlan(plan_id="p1",timestamp=0.0,envelope_id="e1",metadata=SubmissionMetadata(submission_id="s1"),stages=[SubmissionStage(name="test",status="done")],references=GatewayReference())
    r=v.validate(p); assert r["valid"] is True

def test_registry_init():
    assert GatewayRegistry() is not None
def test_registry_count():
    r=GatewayRegistry(); r.register(ApprovalGatewayRequest(request_id="r1",timestamp=0.0)); assert r.count==1

def test_gateway_init():
    assert ApprovalGateway() is not None
def test_gateway_process():
    g=ApprovalGateway()
    p=ApprovalSubmissionPlan(plan_id="p1",timestamp=0.0,envelope_id="e1",ready=True,metadata=SubmissionMetadata(submission_id="s1"),stages=[SubmissionStage(name="s",status="done")])
    r=g.process(p); assert r.success is True
    assert g.gateway_count==1

def test_runtime_gateway():
    r=DecisionRuntimeV3()
    src={"package_id":"p1","metadata":{"version":"1.0"},"total_sections":2,"decision_input_id":"d1","justification_id":"j1",
         "sections":{"decision_input":{"input_id":"d1","timestamp":100.0,"priority_score":2,"confidence":80.0,"candidates":[{"runtime_id":"r1","action_type":"monitor"}]},"justification":{"summary":"t"}}}
    res=r.consume(src); st=r.get_status(); assert st["gateway_count"]>=1

def test_conversation():
    r=DecisionRuntimeV3(); assert r.conversation_gateway.query_count==10
def test_dashboard():
    r=DecisionRuntimeV3(); assert r.dashboard_gateway.card_count==6

def test_forbidden():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    fs=["gateway_request.py","approval_gateway.py","gateway_router.py","gateway_validator.py","gateway_registry.py","conversation_gateway.py","dashboard_gateway.py","runtime_v3.py"]
    for fn in fs: p=os.path.join(dp,fn)
    for pat in ["import threading","import asyncio","async def","await ","import socket"]:
        for fn in fs:
            p=os.path.join(dp,fn)
            if os.path.exists(p):
                with open(p,"r",encoding="utf-8") as f: assert pat not in f.read(), f"{pat} in {fn}"
def test_no_async():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    for fn in ["gateway_request.py","approval_gateway.py","gateway_router.py","gateway_validator.py","gateway_registry.py","conversation_gateway.py","dashboard_gateway.py","runtime_v3.py"]:
        p=os.path.join(dp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: t=f.read(); assert "async def" not in t; assert "await " not in t

@pytest.mark.parametrize("i",range(100))
def test_deterministic_gateway(i):
    r=DecisionRuntimeV3()
    src={"package_id":f"p{i}","metadata":{"version":"1.0"},"total_sections":1,
         "sections":{"decision_input":{"input_id":f"d{i}","timestamp":float(i),"priority_score":i%4,"confidence":50.0+float(i%5)*10,
                                         "candidates":[{"runtime_id":"r1","action_type":"monitor"}]}}}
    res=r.consume(src); assert res["received"] is True
