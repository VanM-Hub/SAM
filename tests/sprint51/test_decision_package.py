import pytest, os
from dataclasses import FrozenInstanceError
from sam.guardian.live.decision_package import DecisionPackage,PackageMetadata,PackageStatistics,PackageSnapshot,PackageVersion,PackageSummary
from sam.guardian.live.package_builder import PackageBuilder
from sam.guardian.live.package_validator import PackageValidator,PackageValidationResult
from sam.guardian.live.package_serializer import PackageSerializer
from sam.guardian.live.package_registry import PackageRegistry
from sam.guardian.live.decision_input import DecisionInput

def test_dto_frozen():
    p=DecisionPackage(package_id="p1")
    with pytest.raises(FrozenInstanceError): p.package_id="x"
def test_meta_frozen():
    m=PackageMetadata(package_id="p1")
    with pytest.raises(FrozenInstanceError): m.package_id="x"
def test_pkg_version():
    assert str(PackageVersion.current())=="1.0"
def test_pkg_to_dict():
    m=PackageMetadata(package_id="p1",version="1.0")
    p=DecisionPackage(package_id="p1",metadata=m,sections={"a":"b"},total_sections=1)
    d=p.to_dict(); assert d["total_sections"]==1

def test_builder_init():
    assert PackageBuilder() is not None
def test_builder_build():
    b=PackageBuilder()
    d=DecisionInput(input_id="d1",timestamp=0.0)
    p=b.build(decision_input=d,runtime_id="r1")
    assert p.decision_input_id=="d1"
    assert p.total_sections>=1
    assert p.metadata is not None

def test_validator_init():
    assert PackageValidator() is not None
def test_validator_valid():
    v=PackageValidator()
    m=PackageMetadata(package_id="p1",version="1.0")
    p=DecisionPackage(package_id="p1",metadata=m,sections={"decision_input":{},"justification":{}},total_sections=2,decision_input_id="d1",justification_id="j1")
    r=v.validate(p); assert r.valid is True
def test_validator_missing():
    v=PackageValidator()
    p=DecisionPackage(package_id="p1",total_sections=0)
    r=v.validate(p); assert r.valid is False

def test_serializer_init():
    assert PackageSerializer() is not None
def test_serializer_to_dict():
    s=PackageSerializer()
    p=DecisionPackage(package_id="p1")
    d=s.to_dict(p); assert d["package_id"]=="p1"
def test_serializer_summary():
    s=PackageSerializer()
    m=PackageMetadata(package_id="p1",version="1.0")
    p=DecisionPackage(package_id="p1",metadata=m,sections={"a":1},total_sections=1,decision_input_id="d1")
    sm=s.summary(p); assert sm["has_decision_input"] is True

def test_registry_init():
    r=PackageRegistry(); assert r.count==0; assert r.latest is None
def test_registry_register():
    r=PackageRegistry()
    p=DecisionPackage(package_id="p1")
    r.register(p); assert r.count==1; assert r.latest is not None
def test_registry_lookup():
    r=PackageRegistry()
    p=DecisionPackage(package_id="find-me")
    r.register(p); assert r.lookup("find-me") is not None
def test_registry_statistics():
    r=PackageRegistry()
    m=PackageMetadata(package_id="p1",version="1.0")
    p=DecisionPackage(package_id="p1",metadata=m,sections={"a":1},total_sections=1)
    r.register(p); s=r.get_statistics(); assert s.total==1

def test_conv_query():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r=GuardianLiveRuntime(runtime_id="pc-q"); assert r.conversation_package.query_count==10
def test_conv_package():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r=GuardianLiveRuntime(runtime_id="pc-l"); assert r.conversation_package.latest_package()["has_package"] is False

def test_dash_count():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    r=GuardianLiveRuntime(runtime_id="pd-c"); assert r.dashboard_package.card_count==6

def test_pipeline_package():
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber
    class PSub(GuardianEventSubscriber):
        def supports(self,e): return True
        def handle(self,e): return {"h":True}
    r=GuardianLiveRuntime(runtime_id="pipe-pkg"); r.start(); r.register_subscriber(PSub())
    r.execute_pipeline({"x":1}); r.execute_pipeline({"x":2})
    st=r.get_status(); assert "package_count" in st; r.stop()

def test_forbidden():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); lp=os.path.join(root,"src","sam","guardian","live")
    fs=["decision_package.py","package_builder.py","package_validator.py","package_serializer.py","package_registry.py","conversation_package.py","dashboard_package.py"]
    for pat in ["from sam.domain","from sam.repository","from sam.storage","from sam.operations","import threading","import asyncio","async def","await ","import socket"]:
        for fn in fs:
            p=os.path.join(lp,fn)
            if os.path.exists(p):
                with open(p,"r",encoding="utf-8") as f: assert pat not in f.read(), f"{pat} in {fn}"
def test_no_async():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","..")); lp=os.path.join(root,"src","sam","guardian","live")
    for fn in ["decision_package.py","package_builder.py","package_validator.py","package_serializer.py","package_registry.py","conversation_package.py","dashboard_package.py"]:
        p=os.path.join(lp,fn)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8") as f: t=f.read(); assert "async def" not in t; assert "await " not in t

@pytest.mark.parametrize("i",range(80))
def test_deterministic_pkg(i):
    from sam.guardian.live.runtime import GuardianLiveRuntime
    from sam.guardian.live.subscriber import GuardianEventSubscriber
    class DSub(GuardianEventSubscriber):
        def supports(self,e): return True
        def handle(self,e): return {"i":i}
    r=GuardianLiveRuntime(runtime_id=f"det-pkg-{i:03d}"); r.start(); r.register_subscriber(DSub())
    for _ in range(2): r.execute_pipeline({"i":i})
    r.stop()
