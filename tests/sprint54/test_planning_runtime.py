import pytest, os
from dataclasses import FrozenInstanceError
from sam.operations.brain.decision.planning import DecisionPlan,DecisionAlternative,PlanningStage,PlanningSummary,PlanningStatistics,PlanningSnapshot
from sam.operations.brain.decision.planner import DecisionPlanner
from sam.operations.brain.decision.planning_alternatives import AlternativeGeneratorS54
from sam.operations.brain.decision.strategy import StrategyBuilder
from sam.operations.brain.decision.constraints import ConstraintEngine
from sam.operations.brain.decision.evaluation import DecisionEvaluation,EvaluationResult,ReadinessLevel,ConfidenceLevel
from sam.operations.brain.decision.runtime_v3 import DecisionRuntimeV3

def test_dto_frozen():
    p=DecisionPlan(plan_id="p1",timestamp=0.0,evaluation_id="e1")
    with pytest.raises(FrozenInstanceError): p.plan_id="x"
def test_alt_frozen():
    a=DecisionAlternative(alternative_id="a1")
    with pytest.raises(FrozenInstanceError):
        a.alternative_id="x"
def test_stage_frozen():
    s=PlanningStage(name="s")
def test_summary_frozen():
    s=PlanningSummary()
    with pytest.raises(FrozenInstanceError):
        s.total=5
def test_alt_to_dict():
    a=DecisionAlternative(alternative_id="a1",description="test",readiness="READY")
    d=a.to_dict(); assert d["readiness"]=="READY"

def test_generator_init():
    assert AlternativeGeneratorS54() is not None
def test_generator_ready():
    g=AlternativeGeneratorS54()
    e=DecisionEvaluation(evaluation_id="e1",timestamp=0.0,context_id="c1",ready=ReadinessLevel.READY,confidence=ConfidenceLevel.VERY_HIGH)
    alts=g.generate(e); assert len(alts)>=2

def test_strategy_init():
    assert StrategyBuilder() is not None
def test_strategy_ready():
    s=StrategyBuilder()
    e=DecisionEvaluation(evaluation_id="e1",timestamp=0.0,context_id="c1",ready=ReadinessLevel.READY,confidence=ConfidenceLevel.VERY_HIGH,
                         overall_result=EvaluationResult(passed=True,score=0.9))
    strat=s.build(e); assert strat["approach"]=="direct_execution"

def test_constraints_init():
    assert ConstraintEngine() is not None
def test_constraints_ready():
    c=ConstraintEngine()
    e=DecisionEvaluation(evaluation_id="e1",timestamp=0.0,context_id="c1",ready=ReadinessLevel.READY,confidence=ConfidenceLevel.VERY_HIGH,
                         policy_result=EvaluationResult(passed=True))
    r=c.check(e); assert r["can_proceed"] is True

def test_planner_init():
    assert DecisionPlanner() is not None
def test_planner_plan():
    pl=DecisionPlanner()
    e=DecisionEvaluation(evaluation_id="e1",timestamp=0.0,context_id="c1",ready=ReadinessLevel.READY,confidence=ConfidenceLevel.HIGH,
                         policy_result=EvaluationResult(passed=True))
    plan=pl.plan(e)
    assert plan.evaluation_id=="e1"
    assert len(plan.alternatives)>=2
    assert plan.recommended is not None

def test_runtime_init():
    r=DecisionRuntimeV3(); st=r.get_status(); assert st["plan_count"]==0
def test_runtime_plan():
    r=DecisionRuntimeV3()
    src={"package_id":"p1","metadata":{"version":"1.0"},"total_sections":2,"decision_input_id":"d1","justification_id":"j1",
         "sections":{"decision_input":{"input_id":"d1","timestamp":100.0,"priority_score":2,"confidence":80.0,"candidates":[{"runtime_id":"r1","action_type":"monitor"}]},"justification":{"summary":"t"}}}
    res=r.consume(src); assert "plan_alternatives" in res; st=r.get_status(); assert st["has_plan"] is True

def test_conversation():
    r=DecisionRuntimeV3(); assert r.conversation_plan.query_count==10
def test_dashboard():
    r=DecisionRuntimeV3(); assert r.dashboard_plan.card_count==6

def test_forbidden():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    fs=["planning.py","planner.py","planning_alternatives.py","strategy.py","constraints.py","conversation_planning.py","dashboard_planning.py","runtime_v3.py"]
    for pat in ["import threading","import asyncio","async def","await ","import socket"]:
        for fn in fs:
            p=os.path.join(dp,fn)
            if os.path.exists(p):
                with open(p,"r",encoding="utf-8") as f: assert pat not in f.read(), f"{pat} in {fn}"
def test_no_async():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    for fn in ["planning.py","planner.py","planning_alternatives.py","strategy.py","constraints.py","conversation_planning.py","dashboard_planning.py","runtime_v3.py"]:
        p=os.path.join(dp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: t=f.read(); assert "async def" not in t; assert "await " not in t

@pytest.mark.parametrize("i",range(100))
def test_deterministic_plan(i):
    r=DecisionRuntimeV3()
    src={"package_id":f"p{i}","metadata":{"version":"1.0"},"total_sections":1,
         "sections":{"decision_input":{"input_id":f"d{i}","timestamp":float(i),"priority_score":i%4,"confidence":50.0+float(i%5)*10,
                                         "candidates":[{"runtime_id":"r1","action_type":"monitor"}]}}}
    res=r.consume(src); assert res["received"] is True

