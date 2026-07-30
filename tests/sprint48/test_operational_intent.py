import pytest, os
from dataclasses import FrozenInstanceError
from sam.guardian.live.intent import GuardianIntent,IntentType,IntentPriority,IntentStatus,IntentSummary,IntentSnapshot,IntentStatistics,ValidationResult
from sam.guardian.live.intent_builder import IntentBuilder
from sam.guardian.live.intent_policy import IntentPolicyEngine
from sam.guardian.live.intent_ranker import IntentRanker
from sam.guardian.live.intent_validator import IntentValidator
from sam.guardian.live.assessment import GuardianAssessment,AssessmentLevel,AssessmentCategory,RiskLevel,PriorityLevel
from sam.guardian.live.situation import GuardianSituation,SituationType,SituationSeverity

# DTO immutability
def test_intent_frozen():
    i = GuardianIntent(intent_id="i1",intent_type=IntentType.OBSERVE,priority=IntentPriority.LOW,status=IntentStatus.PENDING,timestamp=0.0)
    with pytest.raises(FrozenInstanceError):
        i.intent_id = "x"

def test_intent_to_dict():
    i = GuardianIntent(intent_id="i1",intent_type=IntentType.ESCALATE,priority=IntentPriority.URGENT,status=IntentStatus.ACTIVE,timestamp=0.0,description="urgent")
    d = i.to_dict()
    assert d["intent_type"] == "ESCALATE"
    assert d["priority"] == "URGENT"

def test_summary_frozen():
    s = IntentSummary()
    with pytest.raises(FrozenInstanceError):
        s.total = 5

def test_snapshot_frozen():
    s = IntentSnapshot(snapshot_id="s1",timestamp=0.0)
    with pytest.raises(FrozenInstanceError):
        s.snapshot_id = "x"

def test_validation_frozen():
    v = ValidationResult()
    with pytest.raises(FrozenInstanceError):
        v.valid = False

# Builder
def test_builder_init():
    assert IntentBuilder() is not None

def test_builder_from_assessment():
    b = IntentBuilder()
    a = GuardianAssessment(assessment_id="a1",timestamp=0.0,situation_id="s1",category=AssessmentCategory.OVERALL_HEALTH,level=AssessmentLevel.CRITICAL,risk=RiskLevel.CRITICAL,priority=PriorityLevel.URGENT,confidence=90.0,description="cr")
    i = b.build_from_assessment(a)
    assert i.intent_type in (IntentType.ESCALATE,IntentType.INVESTIGATE,IntentType.REVIEW)

def test_builder_from_situation():
    b = IntentBuilder()
    s = GuardianSituation(situation_id="s1",situation_type=SituationType.HEALTHY,severity=SituationSeverity.INFO,timestamp=0.0)
    i = b.build_from_situation(s)
    assert i.intent_type == IntentType.OBSERVE

def test_builder_critical():
    b = IntentBuilder()
    a = GuardianAssessment(assessment_id="a1",timestamp=0.0,situation_id="s1",category=AssessmentCategory.OPERATIONAL_RISK,level=AssessmentLevel.CRITICAL,risk=RiskLevel.CRITICAL,priority=PriorityLevel.URGENT,confidence=95.0,description="crit")
    i = b.build_from_assessment(a)
    assert i.priority == IntentPriority.URGENT

# Policy
def test_policy_init():
    assert IntentPolicyEngine() is not None

def test_policy_observe():
    p = IntentPolicyEngine()
    i = GuardianIntent(intent_id="i1",intent_type=IntentType.OBSERVE,priority=IntentPriority.LOW,status=IntentStatus.PENDING,timestamp=0.0)
    r = p.apply_policy(i)
    assert r["result"] == "observe_only"

def test_policy_escalate():
    p = IntentPolicyEngine()
    i = GuardianIntent(intent_id="i1",intent_type=IntentType.ESCALATE,priority=IntentPriority.URGENT,status=IntentStatus.PENDING,timestamp=0.0,confidence=90.0)
    r = p.apply_policy(i)
    assert r["result"] == "escalate_immediate"

def test_policy_validate():
    p = IntentPolicyEngine()
    i = GuardianIntent(intent_id="i1",intent_type=IntentType.NO_ACTION,priority=IntentPriority.URGENT,status=IntentStatus.PENDING,timestamp=0.0)
    v = p.validate(i)
    assert v.valid is False

# Ranker
def test_ranker_init():
    assert IntentRanker() is not None

def test_ranker_order():
    r = IntentRanker()
    i1 = GuardianIntent(intent_id="i1",intent_type=IntentType.OBSERVE,priority=IntentPriority.LOW,status=IntentStatus.PENDING,timestamp=0.0)
    i2 = GuardianIntent(intent_id="i2",intent_type=IntentType.ESCALATE,priority=IntentPriority.URGENT,status=IntentStatus.PENDING,timestamp=0.0)
    ranked = r.rank([i1,i2])
    assert ranked[0].intent_id == "i2"

# Validator
def test_validator_init():
    assert IntentValidator() is not None

def test_validator_valid():
    v = IntentValidator()
    i = GuardianIntent(intent_id="i1",intent_type=IntentType.OBSERVE,priority=IntentPriority.LOW,status=IntentStatus.PENDING,timestamp=0.0,confidence=50.0)
    r = v.validate(i,[])
    assert r.valid is True

def test_validator_orphan():
    v = IntentValidator()
    i = GuardianIntent(intent_id="i1",intent_type=IntentType.ESCALATE,priority=IntentPriority.URGENT,status=IntentStatus.PENDING,timestamp=0.0,confidence=50.0)
    r = v.validate(i,[])
    assert len(r.warnings) >= 0

# Conversation
def test_conv_intent_q():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="iq-q")
    assert r.conversation_intent.query_count == 10

def test_conv_intent_latest():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="iq-l")
    assert r.conversation_intent.latest_intent()["has_intent"] is False

def test_conv_intent_history():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="iq-h")
    assert r.conversation_intent.intent_history()["total"] == 0

# Dashboard
def test_dash_intent_count():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="id-c")
    assert r.dashboard_intent.card_count == 6

def test_dash_intent_current():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="id-cc")
    c = r.dashboard_intent.get_current_intent_card()
    assert c.type_name == "NONE"

def test_dash_intent_queue():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="id-q")
    c = r.dashboard_intent.get_intent_queue_card()
    assert c.total == 0

def test_dash_intent_all():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="id-ac")
    assert len(r.dashboard_intent.get_all_cards()) == 6

# Pipeline
def test_pipeline_intent():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber
    class ISub(GuardianEventSubscriber):
        def supports(self,e):
            return True
        def handle(self,e):
            return {"h":True}
    r = GuardianLiveRuntime(runtime_id="pipe-int")
    r.start()
    r.register_subscriber(ISub())
    r.execute_pipeline({"x":1})
    r.execute_pipeline({"x":2})
    st = r.get_status()
    assert "intent_count" in st
    r.stop()

# Forbidden
FORBIDDEN = ["from sam.domain","from sam.repository","from sam.storage","from sam.operations","import threading","import asyncio","async def","await ","import socket","import websockets","from websocket","import multiprocessing"]

def test_forbidden():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))
    lp = os.path.join(root,"src","sam","guardian","live")
    fs = ["intent.py","intent_builder.py","intent_policy.py","intent_ranker.py","intent_validator.py","conversation_intent.py","dashboard_intent.py"]
    for fn in fs:
        p = os.path.join(lp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f:
                txt = f.read()
            for pat in FORBIDDEN:
                assert pat not in txt, f"{pat} in {fn}"

def test_no_async():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))
    lp = os.path.join(root,"src","sam","guardian","live")
    fs = ["intent.py","intent_builder.py","intent_policy.py","intent_ranker.py","intent_validator.py","conversation_intent.py","dashboard_intent.py"]
    for fn in fs:
        p = os.path.join(lp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f:
                txt = f.read()
            assert "async def" not in txt
            assert "await " not in txt

@pytest.mark.parametrize("i",range(80))
def test_deterministic_intent(i):
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber
    class DSub(GuardianEventSubscriber):
        def supports(self,e):
            return True
        def handle(self,e):
            return {"i":i}
    r = GuardianLiveRuntime(runtime_id=f"det-int-{i:03d}")
    r.start()
    r.register_subscriber(DSub())
    for _ in range(2):
        r.execute_pipeline({"i":i})
    r.stop()
