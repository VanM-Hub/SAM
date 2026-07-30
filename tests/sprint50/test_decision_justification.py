import pytest, os, uuid
from dataclasses import FrozenInstanceError
from sam.guardian.live.justification import DecisionJustification,JustificationSection,EvidenceReference,RuleReference,JustificationSummary,JustificationSnapshot
from sam.guardian.live.builder import JustificationBuilder
from sam.guardian.live.evidence_chain import EvidenceChain,EvidenceChainBuilder
from sam.guardian.live.rule_trace import RuleTrace,RuleStep,RuleTracer
from sam.guardian.live.consistency import ConsistencyResult,ConsistencyVerifier
from sam.guardian.live.decision_input import DecisionInput,EligibilityStatus

# DTO
def test_just_frozen():
    j = DecisionJustification(justification_id="j1",timestamp=0.0,decision_input_id="d1",source_intent_id="i1")
    with pytest.raises(FrozenInstanceError): j.justification_id="x"
def test_just_to_dict():
    j = DecisionJustification(justification_id="j1",timestamp=0.0,decision_input_id="d1",source_intent_id="i1",summary="test")
    d = j.to_dict(); assert d["summary"]=="test"
def test_section_frozen():
    s = JustificationSection(title="t")
    with pytest.raises(FrozenInstanceError): s.title="x"
def test_evidence_frozen():
    e = EvidenceReference(step="s")
    with pytest.raises(FrozenInstanceError): e.step="x"
def test_rule_frozen():
    r = RuleReference(rule_name="rn")
    with pytest.raises(FrozenInstanceError): r.rule_name="x"
def test_summary_frozen():
    s = JustificationSummary()
    with pytest.raises(FrozenInstanceError): s.total=5

# Builder
def test_builder_init():
    assert JustificationBuilder() is not None
def test_builder_build():
    b = JustificationBuilder()
    d = DecisionInput(input_id="d1",timestamp=0.0,eligibility=EligibilityStatus.ELIGIBLE,confidence=80.0)
    j = b.build(d)
    assert j.decision_input_id=="d1"
    assert len(j.sections)>=3

# Evidence Chain
def test_chain_init():
    assert EvidenceChainBuilder() is not None
def test_chain_build():
    cb = EvidenceChainBuilder()
    refs = [EvidenceReference(step="handoff",source_id="d1",source_type="DecisionInput",timestamp=0.0)]
    c = cb.build(refs)
    assert c.complete is False
def test_chain_complete():
    cb = EvidenceChainBuilder()
    refs = [EvidenceReference(step=s,source_id="x",source_type="t",timestamp=float(i)) for i,s in enumerate(["observation","transition","situation","assessment","intent","handoff"])]
    c = cb.build(refs)
    assert c.complete is True

# Rule Trace
def test_trace_init():
    assert RuleTracer() is not None
def test_trace_build():
    t = RuleTracer()
    refs = [RuleReference(rule_name="r1",rule_type="mapping",triggered=True)]
    tr = t.trace(refs)
    assert tr.total_rules==1

# Consistency
def test_consistency_init():
    assert ConsistencyVerifier() is not None
def test_consistency_valid():
    v = ConsistencyVerifier()
    j = DecisionJustification(justification_id="j1",timestamp=0.0,decision_input_id="d1",source_intent_id="i1",summary="t",
                              sections=[JustificationSection(title="Overview",evidence=[EvidenceReference(step="h",source_id="d1",source_type="D",timestamp=0.0)])])
    r = v.verify(j); assert r.is_consistent is True
def test_consistency_no_evidence():
    v = ConsistencyVerifier()
    j = DecisionJustification(justification_id="j1",timestamp=0.0,decision_input_id="d1",source_intent_id="i1",summary="t",sections=[JustificationSection(title="Empty")])
    r = v.verify(j); assert r.is_consistent is False

# Conversation
def test_conv_query():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="jc-q"); assert r.conversation_justification.query_count==10
def test_conv_latest():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="jc-l"); assert r.conversation_justification.latest_justification()["has_justification"] is False

# Dashboard
def test_dash_count():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r = GuardianLiveRuntime(runtime_id="jd-c"); assert r.dashboard_justification.card_count==6

# Pipeline
def test_pipeline_just():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber
    class JSub(GuardianEventSubscriber):
        def supports(self,e): return True
        def handle(self,e): return {"h":True}
    r = GuardianLiveRuntime(runtime_id="pipe-just"); r.start(); r.register_subscriber(JSub())
    r.execute_pipeline({"x":1}); r.execute_pipeline({"x":2})
    st = r.get_status(); assert "justification_count" in st; r.stop()

# Forbidden
def test_forbidden():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))
    lp=os.path.join(root,"src","sam","guardian","live")
    fs=["justification.py","builder.py","evidence_chain.py","rule_trace.py","consistency.py","conversation_justification.py","dashboard_justification.py"]
    for pat in ["from sam.domain","from sam.repository","from sam.storage","from sam.operations","import threading","import asyncio","async def","await ","import socket"]:
        for fn in fs:
            p=os.path.join(lp,fn)
            if os.path.exists(p):
                with open(p,"r",encoding="utf-8") as f: assert pat not in f.read(), f"{pat} in {fn}"
def test_no_async():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); lp=os.path.join(root,"src","sam","guardian","live")
    for fn in ["justification.py","builder.py","evidence_chain.py","rule_trace.py","consistency.py","conversation_justification.py","dashboard_justification.py"]:
        p=os.path.join(lp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: t=f.read(); assert "async def" not in t; assert "await " not in t

@pytest.mark.parametrize("i",range(80))
def test_deterministic_just(i):
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber
    class DSub(GuardianEventSubscriber):
        def supports(self,e): return True
        def handle(self,e): return {"i":i}
    r = GuardianLiveRuntime(runtime_id=f"det-just-{i:03d}"); r.start(); r.register_subscriber(DSub())
    for _ in range(2): r.execute_pipeline({"i":i})
    r.stop()
