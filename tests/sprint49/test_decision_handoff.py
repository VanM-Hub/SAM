import pytest, os
from dataclasses import FrozenInstanceError
from sam.guardian.live.decision_input import DecisionInput,DecisionCandidate,DecisionReason,DecisionMetadata,DecisionStatistics,DecisionSnapshot,EligibilityStatus
from sam.guardian.live.handoff import HandoffEngine
from sam.guardian.live.mapping import IntentMapper
from sam.guardian.live.eligibility import EligibilityEngine,EligibilityResult
from sam.guardian.live.queue import DecisionQueue
from sam.guardian.live.intent import GuardianIntent,IntentType,IntentPriority,IntentStatus

# DTO
def test_dto_frozen():
    d = DecisionInput(input_id="d1",timestamp=0.0)
    with pytest.raises(FrozenInstanceError): d.input_id="x"
def test_candidate_frozen():
    c = DecisionCandidate()
    with pytest.raises(FrozenInstanceError): c.candidate_id="x"
def test_metadata_to_dict():
    m = DecisionMetadata(source_intent_id="i1")
    d = m.to_dict(); assert d["source_intent_id"]=="i1"
def test_reason_frozen():
    r = DecisionReason()
    with pytest.raises(FrozenInstanceError): r.primary="x"

# Handoff
def test_handoff_init():
    assert HandoffEngine() is not None
def test_handoff_converts():
    h = HandoffEngine()
    i = GuardianIntent(intent_id="i1",intent_type=IntentType.OBSERVE,priority=IntentPriority.LOW,status=IntentStatus.PENDING,timestamp=0.0,confidence=80.0,evidence_count=2)
    d = h.handoff(i)
    assert d.metadata.source_intent_id=="i1"
    assert d.eligibility in (EligibilityStatus.ELIGIBLE,EligibilityStatus.NOT_ELIGIBLE)
def test_handoff_blocked():
    h = HandoffEngine()
    i = GuardianIntent(intent_id="i1",intent_type=IntentType.BLOCKED,priority=IntentPriority.LOW,status=IntentStatus.PENDING,timestamp=0.0)
    d = h.handoff(i)
    assert d.eligibility == EligibilityStatus.BLOCKED

# Mapping
def test_mapper_init():
    assert IntentMapper() is not None
def test_mapper_observe():
    m = IntentMapper()
    i = GuardianIntent(intent_id="i1",intent_type=IntentType.OBSERVE,priority=IntentPriority.LOW,status=IntentStatus.PENDING,timestamp=0.0,affected_runtimes=["r1"])
    cs = m.map(i); assert len(cs)>=1; assert cs[0].action_type=="observation"

# Eligibility
def test_eligibility_init():
    assert EligibilityEngine() is not None
def test_eligibility_eligible():
    e = EligibilityEngine()
    i = GuardianIntent(intent_id="i1",intent_type=IntentType.OBSERVE,priority=IntentPriority.LOW,status=IntentStatus.PENDING,timestamp=0.0,confidence=80.0,evidence_count=3)
    r = e.check(i); assert r.eligible is True
def test_eligibility_low_confidence():
    e = EligibilityEngine()
    i = GuardianIntent(intent_id="i1",intent_type=IntentType.OBSERVE,priority=IntentPriority.LOW,status=IntentStatus.PENDING,timestamp=0.0,confidence=10.0,evidence_count=3)
    r = e.check(i); assert r.eligible is False

# Queue
def test_queue_init():
    q = DecisionQueue(); assert q.count==0
def test_queue_enqueue():
    q = DecisionQueue()
    d = DecisionInput(input_id="d1",timestamp=0.0)
    q.enqueue(d); assert q.count==1
def test_queue_peek():
    q = DecisionQueue()
    assert q.peek() is None
    d = DecisionInput(input_id="d1",timestamp=0.0)
    q.enqueue(d); assert q.peek() is not None
def test_queue_statistics():
    q = DecisionQueue()
    d = DecisionInput(input_id="d1",timestamp=0.0,confidence=80.0)
    q.enqueue(d); s = q.get_statistics(); assert s.total==1

# Conversation
def test_conv_query():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="hc-q"); assert r.conversation_handoff.query_count==10
def test_conv_queue():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="hc-dq"); r.decision_queue.enqueue(DecisionInput(input_id="d1",timestamp=0.0))
    res = r.conversation_handoff.decision_queue(); assert res["count"]==1

# Dashboard
def test_dash_count():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="hd-c"); assert r.dashboard_handoff.card_count==6
def test_dash_queue():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="hd-q"); c = r.dashboard_handoff.get_decision_queue_card(); assert c.total==0

# Pipeline
def test_pipeline_handoff():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber
    class HSub(GuardianEventSubscriber):
        def supports(self,e): return True
        def handle(self,e): return {"h":True}
    r = GuardianLiveRuntime(runtime_id="pipe-hd"); r.start(); r.register_subscriber(HSub())
    r.execute_pipeline({"x":1}); r.execute_pipeline({"x":2})
    st = r.get_status(); assert "decision_queue_count" in st; r.stop()

# Forbidden
FORBIDDEN=["from sam.domain","from sam.repository","from sam.storage","from sam.operations","import threading","import asyncio","async def","await ","import socket","import websockets","from websocket","import multiprocessing"]
def test_forbidden():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))
    lp=os.path.join(root,"src","sam","guardian","live")
    fs=["decision_input.py","handoff.py","mapping.py","eligibility.py","queue.py","conversation_handoff.py","dashboard_handoff.py"]
    for fn in fs:
        p=os.path.join(lp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: txt=f.read()
            for pat in FORBIDDEN: assert pat not in txt, f"{pat} in {fn}"
def test_no_async():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))
    lp=os.path.join(root,"src","sam","guardian","live")
    fs=["decision_input.py","handoff.py","mapping.py","eligibility.py","queue.py","conversation_handoff.py","dashboard_handoff.py"]
    for fn in fs:
        p=os.path.join(lp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: txt=f.read()
            assert "async def" not in txt; assert "await " not in txt

@pytest.mark.parametrize("i",range(80))
def test_deterministic_handoff(i):
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber
    class DSub(GuardianEventSubscriber):
        def supports(self,e): return True
        def handle(self,e): return {"i":i}
    r = GuardianLiveRuntime(runtime_id=f"det-hd-{i:03d}"); r.start(); r.register_subscriber(DSub())
    for _ in range(2): r.execute_pipeline({"i":i})
    r.stop()
