import pytest, os
from dataclasses import FrozenInstanceError
from sam.guardian.live.assessment import GuardianAssessment, AssessmentLevel, AssessmentCategory, RiskLevel, PriorityLevel, AssessmentSummary, AssessmentStatistics, AssessmentSnapshot
from sam.guardian.live.assessment_builder import AssessmentBuilder
from sam.guardian.live.risk_assessment import RiskAssessor
from sam.guardian.live.priority_assessment import PriorityAssessor
from sam.guardian.live.confidence import ConfidenceEngine
from sam.guardian.live.situation import GuardianSituation, SituationType, SituationSeverity
from sam.guardian.live.transition import RuntimeTransition, TransitionType as TransType, ImpactLevel

# DTO immutability
def test_assessment_frozen():
    a = GuardianAssessment(assessment_id="a1",timestamp=0.0,situation_id="s1",category=AssessmentCategory.OVERALL_HEALTH,
                           level=AssessmentLevel.INFO,risk=RiskLevel.NONE,priority=PriorityLevel.LOW,confidence=50.0,description="t")
    with pytest.raises(FrozenInstanceError): a.assessment_id = "x"
def test_assessment_to_dict():
    a = GuardianAssessment(assessment_id="a1",timestamp=0.0,situation_id="s1",category=AssessmentCategory.OPERATIONAL_RISK,
                           level=AssessmentLevel.CRITICAL,risk=RiskLevel.CRITICAL,priority=PriorityLevel.URGENT,confidence=95.0,description="x")
    d = a.to_dict()
    assert d["level"]=="CRITICAL"; assert d["risk"]=="CRITICAL"; assert d["priority"]=="URGENT"
def test_summary_frozen():
    s = AssessmentSummary(total_assessments=0,category_counts={},level_counts={},risk_counts={},priority_counts={},
                          critical_count=0,warning_count=0,confident_count=0,period_start=0.0,period_end=0.0)
    with pytest.raises(FrozenInstanceError): s.total_assessments = 5
def test_statistics_frozen():
    s = AssessmentStatistics(total=0,by_category={},by_level={},by_risk={},by_priority={},average_confidence=0.0,timestamp=0.0)
    with pytest.raises(FrozenInstanceError): s.total = 5
def test_snapshot_frozen():
    su = AssessmentSummary(total_assessments=0,category_counts={},level_counts={},risk_counts={},priority_counts={},
                           critical_count=0,warning_count=0,confident_count=0,period_start=0.0,period_end=0.0)
    sn = AssessmentSnapshot(snapshot_id="s1",timestamp=0.0,total_active=0,assessments=[],highest_risk="NONE",highest_priority="LOW",summary=su)
    with pytest.raises(FrozenInstanceError): sn.snapshot_id = "x"

# Assessment Builder
def test_builder_init():
    assert AssessmentBuilder() is not None
def test_builder_from_situation():
    b = AssessmentBuilder()
    s = GuardianSituation(situation_id="s1",situation_type=SituationType.HEALTHY,severity=SituationSeverity.INFO,timestamp=0.0)
    a = b.build_from_situation(s)
    assert a.situation_id == "s1"
    assert a.level == AssessmentLevel.POSITIVE
def test_builder_critical_situation():
    b = AssessmentBuilder()
    s = GuardianSituation(situation_id="s2",situation_type=SituationType.RESOURCE_PRESSURE,severity=SituationSeverity.CRITICAL,timestamp=0.0)
    a = b.build_from_situation(s)
    assert a.level == AssessmentLevel.CRITICAL
def test_builder_from_transition():
    b = AssessmentBuilder()
    t = RuntimeTransition(transition_id="t1",transition_type=TransType.RUNTIME_ADDED,runtime_id="r1",timestamp=0.0,impact=ImpactLevel.HIGH)
    a = b.build_from_transition(t)
    assert a.affected_runtimes == ["r1"]

# Risk Assessor
def test_risk_init():
    assert RiskAssessor() is not None
def test_risk_situation():
    ra = RiskAssessor()
    s = GuardianSituation(situation_id="s1",situation_type=SituationType.HEALTHY,severity=SituationSeverity.INFO,timestamp=0.0)
    assert ra.assess_situation(s) == RiskLevel.NONE
def test_risk_critical():
    ra = RiskAssessor()
    s = GuardianSituation(situation_id="s1",situation_type=SituationType.RESOURCE_PRESSURE,severity=SituationSeverity.CRITICAL,timestamp=0.0)
    assert ra.assess_situation(s) == RiskLevel.CRITICAL
def test_risk_all_dimensions():
    ra = RiskAssessor()
    s = GuardianSituation(situation_id="s1",situation_type=SituationType.RUNTIME_INSTABILITY,severity=SituationSeverity.HIGH,timestamp=0.0,affected_runtimes=["r1"])
    r = ra.assess_all(s)
    assert "overall" in r; assert "runtime" in r

# Priority Assessor
def test_priority_init():
    assert PriorityAssessor() is not None
def test_priority_critical():
    pa = PriorityAssessor()
    s = GuardianSituation(situation_id="s1",situation_type=SituationType.HEALTHY,severity=SituationSeverity.CRITICAL,timestamp=0.0)
    assert pa.assess_situation(s) == PriorityLevel.URGENT
def test_priority_low():
    pa = PriorityAssessor()
    s = GuardianSituation(situation_id="s1",situation_type=SituationType.HEALTHY,severity=SituationSeverity.INFO,timestamp=0.0)
    assert pa.assess_situation(s) == PriorityLevel.LOW

# Confidence
def test_confidence_init():
    assert ConfidenceEngine() is not None
def test_confidence_base():
    c = ConfidenceEngine()
    assert c.calculate() == 60.0
def test_confidence_with_transitions():
    c = ConfidenceEngine()
    ts = [RuntimeTransition(transition_id=f"t{i}",transition_type=TransType.RUNTIME_ADDED,runtime_id="r1",timestamp=float(i),impact=ImpactLevel.LOW) for i in range(5)]
    score = c.calculate_from_transitions(ts)
    assert score > 60.0
def test_confidence_interpret():
    c = ConfidenceEngine()
    assert c.interpret(95) == "HIGH_CONFIDENCE"
    assert c.interpret(80) == "GOOD_CONFIDENCE"
    assert c.interpret(60) == "MODERATE_CONFIDENCE"
    assert c.interpret(30) == "LOW_CONFIDENCE"
    assert c.interpret(10) == "POOR_CONFIDENCE"

# Conversation Bridge
def test_conv_assessment_query_count():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ac-q"); assert r.conversation_assessment.query_count == 10
def test_conv_assessment_latest():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ac-l"); res = r.conversation_assessment.latest_assessment()
    assert res["has_assessment"] is False
def test_conv_assessment_risk():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ac-r"); res = r.conversation_assessment.current_risk(); assert "risk" in res
def test_conv_assessment_history():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ac-h"); res = r.conversation_assessment.history(); assert res["total"] == 0
def test_conv_assessment_statistics():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ac-s"); res = r.conversation_assessment.statistics(); assert res["total"] == 0
def test_conv_assessment_critical():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ac-c"); res = r.conversation_assessment.critical_assessment(); assert res["count"] == 0
def test_conv_assessment_overall():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ac-o"); res = r.conversation_assessment.overall_health(); assert res["status"] == "UNKNOWN"

# Dashboard Bridge
def test_dash_assessment_card_count():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ad-c"); assert r.dashboard_assessment.card_count == 6
def test_dash_assessment_overview():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ad-o"); c = r.dashboard_assessment.get_assessment_overview_card(); assert c.total == 0
def test_dash_assessment_risk():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ad-rm"); c = r.dashboard_assessment.get_risk_matrix_card(); assert c.total == 0
def test_dash_assessment_priority():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ad-pm"); c = r.dashboard_assessment.get_priority_matrix_card(); assert isinstance(c.priority_counts,dict)
def test_dash_assessment_confidence():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ad-cf"); c = r.dashboard_assessment.get_confidence_card(); assert c.total == 0
def test_dash_assessment_runtime_risk():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ad-rr"); c = r.dashboard_assessment.get_runtime_risk_card(); assert c.total == 0
def test_dash_assessment_history():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ad-ah"); c = r.dashboard_assessment.get_assessment_history_card(); assert c.total == 0
def test_dash_assessment_all():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="ad-ac"); assert len(r.dashboard_assessment.get_all_cards()) == 6

# Pipeline
def test_pipeline_with_assessment():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber
    class ASub(GuardianEventSubscriber):
        def supports(self,e): return True
        def handle(self,e): return {"h":True}
    r = GuardianLiveRuntime(runtime_id="pipe-as"); r.start(); r.register_subscriber(ASub())
    r.execute_pipeline({"x":1}); r.execute_pipeline({"x":2})
    st = r.get_status()
    assert "assessment_count" in st
    r.stop()

# Forbidden imports
FORBIDDEN = ["from sam.domain","from sam.repository","from sam.storage","from sam.operations",
             "import threading","import asyncio","async def","await ","import socket",
             "import websockets","from websocket","import multiprocessing"]
def test_forbidden():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))
    lp = os.path.join(root,"src","sam","guardian","live")
    files = ["assessment.py","assessment_builder.py","risk_assessment.py","priority_assessment.py","confidence.py","conversation_assessment.py","dashboard_assessment.py"]
    for fn in files:
        p = os.path.join(lp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: txt = f.read()
            for pat in FORBIDDEN: assert pat not in txt, f"{pat} in {fn}"
def test_no_async():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))
    lp = os.path.join(root,"src","sam","guardian","live")
    files = ["assessment.py","assessment_builder.py","risk_assessment.py","priority_assessment.py","confidence.py","conversation_assessment.py","dashboard_assessment.py"]
    for fn in files:
        p = os.path.join(lp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: txt = f.read()
            assert "async def" not in txt; assert "await " not in txt

@pytest.mark.parametrize("i",range(80))
def test_deterministic_assessment(i):
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber
    class DSub(GuardianEventSubscriber):
        def supports(self,e): return True
        def handle(self,e): return {"i":i}
    r = GuardianLiveRuntime(runtime_id=f"det-as-{i:03d}"); r.start(); r.register_subscriber(DSub())
    for _ in range(2): r.execute_pipeline({"i":i})
    r.stop()
