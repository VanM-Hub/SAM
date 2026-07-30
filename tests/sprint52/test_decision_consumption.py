import pytest, os
from dataclasses import FrozenInstanceError
from sam.operations.brain.decision.package_protocol import IncomingDecisionPackage,PackageHeader,PackageBody
from sam.operations.brain.decision.package_consumer import PackageConsumer
from sam.operations.brain.decision.package_normalizer import PackageNormalizer
from sam.operations.brain.decision.package_validator import PackageValidator
from sam.operations.brain.decision.package_context import DecisionContext,DecisionContextBuilder
from sam.operations.brain.decision.runtime_v3 import DecisionRuntimeV3

# DTO
def test_header_frozen():
    h=PackageHeader()
    with pytest.raises(FrozenInstanceError):
        h.source_package_id="x"
def test_body_frozen():
   
    b = PackageBody()
    with pytest.raises(FrozenInstanceError): b.sections={"x":1}
def test_incoming_frozen():
   
    i = IncomingDecisionPackage(package_id="p1")
    with pytest.raises(FrozenInstanceError): i.package_id="x"
def test_context_frozen():
   
    c = DecisionContext()
    with pytest.raises(FrozenInstanceError): c.context_id="x"

# Consumer
def test_consumer_init():
    assert PackageConsumer() is not None
def test_consumer_consume():
    c=PackageConsumer()
    src={"package_id":"p1","metadata":{"version":"1.0","source_component":"GuardianLiveRuntime"},"total_sections":2,"decision_input_id":"d1","justification_id":"j1","sections":{"decision_input":{"input_id":"d1"},"justification":{"summary":"t"}}}
    p=c.consume(src)
    assert p.header.source_package_id=="p1"
    assert p.ready is True

# Normalizer
def test_normalizer_init():
    assert PackageNormalizer() is not None
def test_normalizer_normalize():
    n=PackageNormalizer()
    src={"package_id":"p1","metadata":{"version":"1.0"},"total_sections":0,"sections":{}}
    p=PackageConsumer().consume(src)
    np=n.normalize(p)
    assert np.header.version=="1.0"

# Validator
def test_validator_init():
    assert PackageValidator() is not None
def test_validator_valid():
    v=PackageValidator()
    src={"package_id":"p1","metadata":{"version":"1.0"},"total_sections":1,"decision_input_id":"d1","justification_id":"j1","sections":{"decision_input":{"input_id":"d1","timestamp":100.0},"justification":{"summary":"t"}}}
    p=PackageConsumer().consume(src)
    r=v.validate(p); assert r.valid is True
def test_validator_invalid():
    v=PackageValidator()
    p=IncomingDecisionPackage(package_id="p1")
    r=v.validate(p); assert r.valid is False

# Context
def test_context_builder_init():
    assert DecisionContextBuilder() is not None
def test_context_build():
    b=DecisionContextBuilder()
    src={"package_id":"p1","metadata":{"version":"1.0"},"total_sections":2,"decision_input_id":"d1","justification_id":"j1","sections":{"decision_input":{"input_id":"d1","timestamp":100.0,"priority_score":3,"confidence":90.0,"candidates":[{"runtime_id":"r1","action_type":"monitoring"}]},"justification":{"summary":"t"}}}
    p=PackageConsumer().consume(src)
    c=b.build(p)
    assert c.priority==3; assert c.confidence==90.0; assert "r1" in c.runtime_ids

# Runtime V3
def test_runtime_init():
    r=DecisionRuntimeV3(); st=r.get_status(); assert st["consume_count"]==0
def test_runtime_consume():
    r=DecisionRuntimeV3()
    src={"package_id":"p1","metadata":{"version":"1.0"},"total_sections":2,"decision_input_id":"d1","justification_id":"j1","sections":{"decision_input":{"input_id":"d1","timestamp":100.0,"priority_score":2,"confidence":80.0,"candidates":[{"runtime_id":"r1","action_type":"monitor"}]},"justification":{"summary":"t"}}}
    res=r.consume(src)
    assert res["received"] is True; assert res["valid"] is True; assert res["context_ready"] is True
def test_runtime_conversation():
    r=DecisionRuntimeV3()
    assert r.conversation.query_count==10
def test_runtime_consume_count():
    r=DecisionRuntimeV3()
    src={"package_id":"p1","metadata":{"version":"1.0"},"total_sections":1,"sections":{"decision_input":{"input_id":"d1","timestamp":100.0}}}
    r.consume(src); st=r.get_status(); assert st["consume_count"]==1

# Compatibility: consume from real Guardian package dict
def test_compatibility():
    r=DecisionRuntimeV3()
    guardian_pkg={"package_id":"guardian-1","metadata":{"package_id":"guardian-1","version":"1.0","created_at":100.0,"source_component":"GuardianLiveRuntime","runtime_id":"r1","description":"test"},"total_sections":2,"decision_input_id":"di-1","justification_id":"j-1","sections":{"decision_input":{"input_id":"di-1","timestamp":100.0,"eligibility":"ELIGIBLE","priority_score":2,"confidence":85.0,"candidates":[{"runtime_id":"r1","action_type":"monitor"}]},"justification":{"justification_id":"j-1","summary":"test just"}}}
    res=r.consume(guardian_pkg)
    assert res["received"] is True; st=r.get_status(); assert st["has_latest"] is True

# Dashboard
def test_dash_count():
    r=DecisionRuntimeV3(); assert r.dashboard.card_count==6
def test_dash_cards():
    r=DecisionRuntimeV3()
    src={"package_id":"p1","metadata":{"version":"1.0"},"total_sections":2,"decision_input_id":"d1","justification_id":"j1","sections":{"decision_input":{"input_id":"d1","timestamp":100.0,"priority_score":1,"confidence":75.0},"justification":{"summary":"t"}}}
    r.consume(src)
    cards=r.dashboard.get_all_cards()
    assert len(cards)==6

# Forbidden
def test_forbidden():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    fs=["package_protocol.py","package_consumer.py","package_normalizer.py","package_validator.py","package_context.py","conversation_package.py","dashboard_package.py","runtime_v3.py"]
    for pat in ["import threading","import asyncio","async def","await ","import socket","import websockets","from websocket","import multiprocessing"]:
        for fn in fs:
            p=os.path.join(dp,fn)
            if os.path.exists(p):
                with open(p,"r",encoding="utf-8") as f: assert pat not in f.read(), f"{pat} in {fn}"
def test_no_async():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); dp=os.path.join(root,"src","sam","operations","brain","decision")
    for fn in ["package_protocol.py","package_consumer.py","package_normalizer.py","package_validator.py","package_context.py","conversation_package.py","dashboard_package.py","runtime_v3.py"]:
        p=os.path.join(dp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: t=f.read(); assert "async def" not in t; assert "await " not in t

@pytest.mark.parametrize("i",range(100))
def test_deterministic_consume(i):
    r=DecisionRuntimeV3()
    src={"package_id":f"p{i}","metadata":{"version":"1.0"},"total_sections":1,"sections":{"decision_input":{"input_id":f"d{i}","timestamp":float(i),"priority_score":i%4,"confidence":50.0+float(i%5)*10}}}
    res=r.consume(src)
    assert res["received"] is True


