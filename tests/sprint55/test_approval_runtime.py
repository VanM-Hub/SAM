import pytest, os
from dataclasses import FrozenInstanceError
from sam.operations.brain.decision.approval_preparation import ApprovalPreparation,ApprovalCandidate,ApprovalRequirement,ApprovalMetadata,ApprovalStatistics,ApprovalSnapshot
from sam.operations.brain.decision.approval_builder import ApprovalBuilder
from sam.operations.brain.decision.approval_validator import ApprovalValidator
from sam.operations.brain.decision.approval_requirements import ApprovalRequirementsEngine,ApprovalRequirementSet
from sam.operations.brain.decision.approval_summary import ApprovalSummaryBuilder
from sam.operations.brain.decision.planning import DecisionPlan,DecisionAlternative
from sam.operations.brain.decision.evaluation import DecisionEvaluation,EvaluationResult,ReadinessLevel,ConfidenceLevel
from sam.operations.brain.decision.planner import DecisionPlanner
from sam.operations.brain.decision.runtime_v3 import DecisionRuntimeV3

def test_dto_frozen():
    p=ApprovalPreparation(preparation_id="p1",timestamp=0.0)
    with pytest.raises(FrozenInstanceError): p.preparation_id="x"
def test_candidate_frozen():
    c=ApprovalCandidate(candidate_id="c1")
    with pytest.raises(FrozenInstanceError): c.candidate_id="x"
def test_req_frozen():
    r=ApprovalRequirement(name="r1")
    with pytest.raises(FrozenInstanceError): r.name="x"
def test_meta_frozen():
    m=ApprovalMetadata()
    with pytest.raises(FrozenInstanceError): m.plan_id="x"

def test_builder_init():
    assert ApprovalBuilder() is not None
def test_builder_build():
    b=ApprovalBuilder()
    e=DecisionEvaluation(evaluation_id="e1",timestamp=0.0,context_id="c1",ready=ReadinessLevel.READY,confidence=ConfidenceLevel.VERY_HIGH,
                         policy_result=EvaluationResult(passed=True))
    plan=DecisionPlanner().plan(e)
    prep=b.build(plan)
    assert prep.metadata is not None
    assert len(prep.requirements)>=3

def test_validator_init():
    assert ApprovalValidator() is not None
def test_validator_valid():
    v=ApprovalValidator()
    b=ApprovalBuilder()
    e=DecisionEvaluation(evaluation_id="e1",timestamp=0.0,context_id="c1",ready=ReadinessLevel.READY,confidence=ConfidenceLevel.VERY_HIGH,
                         policy_result=EvaluationResult(passed=True))
    plan=DecisionPlanner().plan(e)
    prep=b.build(plan)
    r=v.validate(prep); assert r.valid is True

def test_requirements_init():
    assert ApprovalRequirementsEngine() is not None
def test_requirements_build():
    e=ApprovalRequirementsEngine()
    reqs=[ApprovalRequirement(name="a",category="mandatory",satisfied=True),ApprovalRequirement(name="b",category="mandatory",satisfied=False)]
    s=e.build(reqs)
    assert "a" in s.mandatory
    assert "b" in s.missing
    assert "b" in s.blocked

def test_summary_init():
    assert ApprovalSummaryBuilder() is not None
def test_summary_build():
    s=ApprovalSummaryBuilder()
    b=ApprovalBuilder()
    e=DecisionEvaluation(evaluation_id="e1",timestamp=0.0,context_id="c1",ready=ReadinessLevel.READY,confidence=ConfidenceLevel.VERY_HIGH,
                         policy_result=EvaluationResult(passed=True))
    plan=DecisionPlanner().plan(e)
    prep=b.build(plan)
    sm=s.build(prep)
    assert "decision" in sm
    assert "recommendation" in sm

def test_runtime_init():
    r=DecisionRuntimeV3(); st=r.get_status(); assert st["approval_count"]==0
def test_runtime_approval():
    r=DecisionRuntimeV3()
    src={"package_id":"p1","metadata":{"version":"1.0"},"total_sections":2,"decision_input_id":"d1","justification_id":"j1",
         "sections":{"decision_input":{"input_id":"d1","timestamp":100.0,"priority_score":2,"confidence":80.0,"candidates":[{"runtime_id":"r1","action_type":"monitor"}]},"justification":{"summary":"t"}}}
    res=r.consume(src); st=r.get_status(); assert st["has_approval"] is True

def test_conversation():
    r=DecisionRuntimeV3(); assert r.conversation_approval.query_count==10
def test_dashboard():
    r=DecisionRuntimeV3(); assert r.dashboard_approval.card_count==6

def test_forbidden():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    fs=["approval_preparation.py","approval_builder.py","approval_validator.py","approval_requirements.py","approval_summary.py","conversation_approval.py","dashboard_approval.py","runtime_v3.py"]
    for pat in ["import threading","import asyncio","async def","await ","import socket"]:
        for fn in fs:
            p=os.path.join(dp,fn)
            if os.path.exists(p):
                with open(p,"r",encoding="utf-8") as f: assert pat not in f.read(), f"{pat} in {fn}"
def test_no_async():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    for fn in ["approval_preparation.py","approval_builder.py","approval_validator.py","approval_requirements.py","approval_summary.py","conversation_approval.py","dashboard_approval.py","runtime_v3.py"]:
        p=os.path.join(dp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: t=f.read(); assert "async def" not in t; assert "await " not in t

@pytest.mark.parametrize("i",range(100))
def test_deterministic_approval(i):
    r=DecisionRuntimeV3()
    src={"package_id":f"p{i}","metadata":{"version":"1.0"},"total_sections":1,
         "sections":{"decision_input":{"input_id":f"d{i}","timestamp":float(i),"priority_score":i%4,"confidence":50.0+float(i%5)*10,
                                         "candidates":[{"runtime_id":"r1","action_type":"monitor"}]}}}
    res=r.consume(src); assert res["received"] is True
