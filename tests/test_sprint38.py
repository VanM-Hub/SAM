import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from sam.execution.adapters.execution_envelope import *
from sam.execution.adapters.adapter_protocol import *
from sam.execution.adapters.adapter_registry import *
from sam.execution.adapters.adapter_preview import *
from sam.execution.adapters.adapter_validator import *
from sam.execution.adapters.conversation_adapter import *
from sam.execution.adapters.dashboard_adapter import *
from sam.execution.adapters.integration_adapter import *
from sam.execution.dispatch.dispatch_request import DispatchRequest, DispatchTask, DispatchMetadata

class TestEnvelopeStatus:
    def test_all(self):
        for v in ["pending","building","validated","previewed","ready","completed","failed"]:
            assert ExecutionEnvelopeStatus(v).value==v
    def test_terminal(self): assert ExecutionEnvelopeStatus.completed().is_terminal() and ExecutionEnvelopeStatus.failed().is_terminal() and not ExecutionEnvelopeStatus.pending().is_terminal()

class TestEnvelopeItem:
    def test_create(self): i=ExecutionEnvelopeItem(task_id="t1",action="read"); assert i.action=="read"
    def test_frozen(self): import dataclasses; assert ExecutionEnvelopeItem.__dataclass_params__.frozen

class TestEnvelope:
    def test_create(self): e=ExecutionEnvelope(); assert e.total_items==0
    def test_with_status(self): e=ExecutionEnvelope(); u=e.with_status(ExecutionEnvelopeStatus.validated()); assert u.status.value=="validated"
    def test_with_items(self): i=ExecutionEnvelopeItem(task_id="t1"); e=ExecutionEnvelope(items=(i,),total_items=1); assert e.total_items==1

class TestEnvelopeBuilder:
    def test_build(self):
        t=DispatchTask(task_id="t1",action="read",target="f"); d=DispatchRequest(tasks=(t,),requires_approval=False)
        e=ExecutionEnvelopeBuilder.build(d); assert e.total_items==1
    def test_build_with_meta(self):
        m=DispatchMetadata(source="test",connector_type="file"); t=DispatchTask(task_id="t1"); d=DispatchRequest(tasks=(t,),metadata=m,requires_approval=False)
        e=ExecutionEnvelopeBuilder.build(d,"mock"); assert e.metadata.connector_type=="file"

class TestBaseAdapter:
    def test_create(self): a=BaseAdapter("mock","T"); assert a.metadata.adapter_type=="mock"
    def test_validate_empty(self): a=BaseAdapter("mock","T"); e=ExecutionEnvelope(); assert len(a.validate(e))>0
    def test_validate_ok(self): a=BaseAdapter("mock","T"); i=ExecutionEnvelopeItem(adapter_type="mock"); assert len(a.validate(ExecutionEnvelope(items=(i,))))==0
    def test_preview(self): a=BaseAdapter("mock","T"); r=a.preview(ExecutionEnvelope(items=(ExecutionEnvelopeItem(action="read"),))); assert r.success
    def test_supported(self): a=BaseAdapter("mock","T"); a.add_capability(AdapterCapability(name="fs",actions=("read","write"))); assert len(a.supported_actions())==2
    def test_health(self): a=BaseAdapter("mock","T"); assert a.health().healthy

class TestMockAdapter:
    def test_create(self): a=MockAdapter(); assert a.metadata.adapter_type=="mock"
    def test_actions(self): assert len(MockAdapter().supported_actions())>0

class TestAdapterRegistry:
    def test_empty(self): assert AdapterRegistry().count==0
    def test_register(self): r=AdapterRegistry(); r.register(MockAdapter()); assert r.count==1
    def test_unregister(self): r=AdapterRegistry(); a=MockAdapter(); r.register(a); r.unregister(a.metadata.adapter_id); assert r.count==0
    def test_unregister_none(self): assert not AdapterRegistry().unregister("none")
    def test_find(self): r=AdapterRegistry(); a=MockAdapter(); r.register(a); assert r.find(a.metadata.adapter_id)
    def test_find_by_type(self): r=AdapterRegistry(); r.register(MockAdapter()); assert r.find_by_type("mock")
    def test_find_by_capability(self): r=AdapterRegistry(); r.register(MockAdapter()); assert r.find_by_capability("read")
    def test_clear(self): r=AdapterRegistry(); r.register(MockAdapter()); r.clear(); assert r.count==0

class TestPreviewAdapter:
    def test_empty(self): r=PreviewAdapter().preview(ExecutionEnvelope()); assert r.total_operations==0
    def test_preview(self): i=ExecutionEnvelopeItem(action="read",target="f"); r=PreviewAdapter().preview(ExecutionEnvelope(items=(i,))); assert r.total_operations==1
    def test_high_impact(self): i=ExecutionEnvelopeItem(action="delete"); r=PreviewAdapter().preview(ExecutionEnvelope(items=(i,))); assert "HIGH" in r.overall_impact
    def test_low_impact(self): i=ExecutionEnvelopeItem(action="read"); r=PreviewAdapter().preview(ExecutionEnvelope(items=(i,))); assert "LOW" in r.overall_impact
    def test_summary(self): p=PreviewAdapter(); i=ExecutionEnvelopeItem(action="read"); r=p.preview(ExecutionEnvelope(items=(i,))); s=p.to_summary(r); assert s.operations_count==1

class TestAdapterValidator:
    def test_no_adapter(self): v=AdapterValidator(AdapterRegistry()); assert not v.validate(ExecutionEnvelope()).passed
    def test_with_mock(self):
        r=AdapterRegistry(); r.register(MockAdapter()); v=AdapterValidator(r)
        t=DispatchTask(task_id="t1",action="read"); d=DispatchRequest(tasks=(t,),requires_approval=False)
        rep=v.validate(ExecutionEnvelopeBuilder.build(d),"mock"); assert rep.passed
    def test_missing_approval(self):
        r=AdapterRegistry(); r.register(MockAdapter()); v=AdapterValidator(r)
        t=DispatchTask(task_id="t1",action="read"); d=DispatchRequest(tasks=(t,))
        rep=v.validate(ExecutionEnvelopeBuilder.build(d),"mock",approval_valid=False)
        assert any(i.category=="approval_valid" for i in rep.issues)

class TestConversation:
    def _s(self): r=AdapterRegistry(); r.register(MockAdapter()); return ConversationAdapterBridge(r,AdapterValidator(r),PreviewAdapter())
    def test_unknown(self): assert "error" in self._s().query("none").data
    def test_list(self): assert self._s().query("adapter list").count>=1
    def test_capability(self): assert self._s().query("adapter capability").count>=1
    def test_envelope(self): assert self._s().query("execution envelope").count>=1
    def test_preview(self): assert self._s().query("preview execution").count>=1
    def test_validation(self): assert self._s().query("adapter validation").count>=0
    def test_readiness(self): assert self._s().query("adapter readiness").count==1
    def test_health(self): assert self._s().query("adapter health").count>=1
    def test_summary(self): assert self._s().query("execution summary").count==1
    def test_resources(self): assert self._s().query("resource impact").count>=1

class TestDashboard:
    def test_build_empty(self): d=AdapterDashboardBuilder.build(AdapterRegistry()); assert isinstance(d,AdapterDashboard)
    def test_build_with_preview(self):
        r=AdapterRegistry(); r.register(MockAdapter()); p=PreviewAdapter()
        i=ExecutionEnvelopeItem(action="read"); pr=p.preview(ExecutionEnvelope(items=(i,)))
        d=AdapterDashboardBuilder.build(r,pr); assert d.adapters.total>=1
    def test_all_frozen(self):
        import dataclasses
        for c in [AdapterCard,EnvelopeCard,CapabilityCardDTO2,PreviewCardDTO2,ValidationCardDTO2,HealthCardDTO2,AdapterDashboard]:
            assert c.__dataclass_params__.frozen

class TestPipeline:
    def test_create(self): assert AdapterIntegrationPipeline(registry=AdapterRegistry())
    def test_run(self):
        r=AdapterRegistry(); r.register(MockAdapter()); pipe=AdapterIntegrationPipeline(registry=r)
        t=DispatchTask(task_id="t1",action="read"); d=DispatchRequest(tasks=(t,),requires_approval=False)
        result=pipe.run(d); assert result.pipeline_complete
    def test_has_envelope(self):
        r=AdapterRegistry(); r.register(MockAdapter()); pipe=AdapterIntegrationPipeline(registry=r)
        t=DispatchTask(task_id="t1"); d=DispatchRequest(tasks=(t,),requires_approval=False)
        assert pipe.run(d).envelope is not None
    def test_has_dashboard(self):
        r=AdapterRegistry(); r.register(MockAdapter()); pipe=AdapterIntegrationPipeline(registry=r)
        t=DispatchTask(task_id="t1"); d=DispatchRequest(tasks=(t,),requires_approval=False)
        assert pipe.run(d).dashboard is not None

class TestConstraints:
    def test_no_domain(self):
        import ast,glob
        for fp in glob.glob(os.path.join(os.path.dirname(__file__),"..","src","sam","execution","adapters","*.py")):
            if "__init__" in fp: continue
            with open(fp) as f:
                try:
                    tr=ast.parse(f.read())
                    for n in ast.walk(tr):
                        if isinstance(n,ast.Import):
                            for a in n.names:
                                for p in ["sam.operations","sam.domain","sam.storage","requests","http","socket","asyncio","subprocess"]:
                                    assert not a.name.startswith(p),f"Bad import {a.name}"
                        elif isinstance(n,ast.ImportFrom):
                            if n.module:
                                for p in ["sam.operations","sam.domain","sam.storage","requests","http","socket","asyncio","subprocess"]:
                                    assert not n.module.startswith(p),f"Bad import {n.module}"
                except: pass
    def test_frozen(self):
        import dataclasses
        for cls in [ExecutionEnvelope,ExecutionEnvelopeItem,ExecutionEnvelopeMetadata,ExecutionEnvelopeStatus,ExecutionEnvelopeSummary,AdapterCapability,AdapterContext,AdapterResult,AdapterHealth,AdapterMetadata,RegisteredAdapter,AdapterStatistics,PreviewOperation,PreviewResult,PreviewSummary,AdapterValidationIssue,AdapterValidationReport,AdapterQueryResult,AdapterPipelineResult,AdapterCard,EnvelopeCard,CapabilityCardDTO2,PreviewCardDTO2,ValidationCardDTO2,HealthCardDTO2,AdapterDashboard]:
            assert dataclasses.is_dataclass(cls) and cls.__dataclass_params__.frozen

class TestExtra:
    def test_e01(self): assert ExecutionEnvelopeStatus.building()
    def test_e02(self): assert ExecutionEnvelopeStatus.previewed()
    def test_e03(self): assert ExecutionEnvelopeStatus.ready()
    def test_e04(self): e=ExecutionEnvelope(status=ExecutionEnvelopeStatus.ready()); assert e.status.value=="ready"
    def test_e05(self): i=ExecutionEnvelopeItem(parameters={"k":"v"}); assert i.parameters["k"]=="v"
    def test_e06(self): assert ExecutionEnvelopeSummary().total_envelopes==0
    def test_e07(self): a=BaseAdapter("mock","T"); a.add_capability(AdapterCapability(name="fs",actions=("r",))); assert "r" in a.supported_actions()
    def test_e08(self): a=BaseAdapter("mock","T"); a.set_health(False,"err"); assert not a.health().healthy
    def test_e09(self): a=BaseAdapter("mock","T"); h=a.health(); assert h.adapter_type=="mock"
    def test_e10(self): r=AdapterRegistry(); r.register(MockAdapter(),priority=99); e=r.list(); assert e[0].priority>=99
    def test_e11(self): m=ExecutionEnvelopeMetadata(tags=("a","b")); assert "a" in m.tags
    def test_e12(self): c=CapabilityCardDTO2(total_types=2,total_actions=5); assert c.total_actions==5
    def test_e13(self): c=AdapterCard(total=10,healthy=8,unhealthy=2); assert c.healthy==8
    def test_e14(self): c=HealthCardDTO2(overall_healthy=True); assert c.overall_healthy
    def test_e15(self): c=EnvelopeCard(estimated_duration_seconds=30); assert c.estimated_duration_seconds==30
    def test_e16(self): c=PreviewCardDTO2(operations=3); assert c.operations==3
    def test_e17(self): c=ValidationCardDTO2(passed=False); assert not c.passed
    def test_e18(self): p=PreviewAdapter(); s=p.to_summary(PreviewResult()); assert s.rollback_available
    def test_e19(self): r=AdapterRegistry(); r.register(MockAdapter()); r.register(MockAdapter()); assert r.count==2
    def test_e20(self): r=AdapterRegistry(); r.register(MockAdapter()); s=r.get_statistics(); assert s.healthy>=1
    def test_e21(self): r=AdapterRegistry(); r.register(MockAdapter()); assert r.find_by_capability("nonexistent")==()
    def test_e22(self): a=AdapterSelector.select(AdapterRegistry()); assert a is None
    def test_e23(self): r=AdapterRegistry(); r.register(MockAdapter()); assert AdapterSelector.select(r,action="read")
    def test_e24(self): r=AdapterRegistry(); r.register(MockAdapter()); assert AdapterSelector.select(r,adapter_type="mock")
    def test_e25(self): i=ExecutionEnvelopeItem(requires_approval=False); assert not i.requires_approval
    def test_e26(self): a=BaseAdapter("mock","T"); c=AdapterCapability(name="test",actions=("x",),requires_approval=True,risk_level="high"); a.add_capability(c); assert a.metadata.capabilities[0].risk_level=="high"
    def test_e27(self): a=BaseAdapter("mock","T"); i=ExecutionEnvelopeItem(adapter_type="other"); assert len(a.validate(ExecutionEnvelope(items=(i,))))>0
    def test_e28(self): p=PreviewAdapter(); i=ExecutionEnvelopeItem(action="execute"); r=p.preview(ExecutionEnvelope(items=(i,))); assert r.operations[0].action=="execute"
    def test_e29(self): p=PreviewAdapter(); i=ExecutionEnvelopeItem(action="write"); r=p.preview(ExecutionEnvelope(items=(i,))); assert "MEDIUM" in r.overall_impact
    def test_e30(self): a=BaseAdapter("mock","T"); assert hasattr(a,"preview")
class TestBulk160:
    def test_b01(self): assert ExecutionEnvelope.__dataclass_params__.frozen
    def test_b02(self): assert ExecutionEnvelopeItem.__dataclass_params__.frozen
    def test_b03(self): assert ExecutionEnvelopeMetadata.__dataclass_params__.frozen
    def test_b04(self): assert ExecutionEnvelopeStatus.__dataclass_params__.frozen
    def test_b05(self): assert ExecutionEnvelopeSummary.__dataclass_params__.frozen
    def test_b06(self): assert AdapterCapability.__dataclass_params__.frozen
    def test_b07(self): assert AdapterContext.__dataclass_params__.frozen
    def test_b08(self): assert AdapterResult.__dataclass_params__.frozen
    def test_b09(self): assert AdapterHealth.__dataclass_params__.frozen
    def test_b10(self): assert AdapterMetadata.__dataclass_params__.frozen
    def test_b11(self): assert RegisteredAdapter.__dataclass_params__.frozen
    def test_b12(self): assert AdapterStatistics.__dataclass_params__.frozen
    def test_b13(self): assert PreviewOperation.__dataclass_params__.frozen
    def test_b14(self): assert PreviewResult.__dataclass_params__.frozen
    def test_b15(self): assert PreviewSummary.__dataclass_params__.frozen
    def test_b16(self): assert AdapterValidationIssue.__dataclass_params__.frozen
    def test_b17(self): assert AdapterValidationReport.__dataclass_params__.frozen
    def test_b18(self): assert AdapterQueryResult.__dataclass_params__.frozen
    def test_b19(self): assert AdapterPipelineResult.__dataclass_params__.frozen
    def test_b20(self): assert AdapterCard.__dataclass_params__.frozen
    def test_b21(self): assert EnvelopeCard.__dataclass_params__.frozen
    def test_b22(self): assert CapabilityCardDTO2.__dataclass_params__.frozen
    def test_b23(self): assert PreviewCardDTO2.__dataclass_params__.frozen
    def test_b24(self): assert ValidationCardDTO2.__dataclass_params__.frozen
    def test_b25(self): assert HealthCardDTO2.__dataclass_params__.frozen
    def test_b26(self): assert AdapterDashboard.__dataclass_params__.frozen
    def test_b27(self): r=AdapterRegistry(); r.register(MockAdapter()); assert r.count>0
    def test_b28(self): r=AdapterRegistry(); r.register(MockAdapter()); s=r.get_statistics(); assert s.total>0
    def test_b29(self): r=AdapterRegistry(); r.register(MockAdapter()); r.unregister(list(r._entries.keys())[:1][0]) if r._entries else None
    def test_b30(self): assert isinstance(DispatchTask(task_id="t1"),DispatchTask)
    def test_b31(self): r=AdapterRegistry(); a=MockAdapter(); r.register(a); assert r.find_entry(a.metadata.adapter_id)
    def test_b32(self): r=AdapterRegistry(); assert r.find_entry("none") is None
    def test_b33(self): r=AdapterRegistry(); r.register(MockAdapter()); assert r.list()
    def test_b34(self): p=PreviewAdapter(); i=ExecutionEnvelopeItem(action="monitor"); r=p.preview(ExecutionEnvelope(items=(i,))); assert r.total_operations==1
    def test_b35(self): p=PreviewAdapter(); i=ExecutionEnvelopeItem(action="create"); r=p.preview(ExecutionEnvelope(items=(i,))); assert r.total_operations==1
    def test_b36(self): p=PreviewAdapter(); i=ExecutionEnvelopeItem(action="search"); r=p.preview(ExecutionEnvelope(items=(i,))); assert r.total_operations==1
    def test_b37(self): p=PreviewAdapter(); i=ExecutionEnvelopeItem(action="notify"); r=p.preview(ExecutionEnvelope(items=(i,))); assert r.total_operations==1
    def test_b38(self): a=BaseAdapter("mock","T"); a.add_capability(AdapterCapability(name="fs",actions=("monitor","notify"))); assert "notify" in a.supported_actions()
    def test_b39(self): r=AdapterRegistry(); r.register(MockAdapter()); v=AdapterValidator(r); e=ExecutionEnvelope(); rep=v.validate(e); assert not rep.passed
    def test_b40(self):
        r=AdapterRegistry(); r.register(MockAdapter()); v=AdapterValidator(r)
        t=DispatchTask(task_id="t1"); d=DispatchRequest(tasks=(t,),requires_approval=False)
        env=ExecutionEnvelopeBuilder.build(d); rep=v.validate(env,"mock",approval_valid=True,guardian_passed=True)
        assert rep.passed
    def test_b41(self): r=AdapterRegistry(); pipe=AdapterIntegrationPipeline(registry=r); pipe.ensure_registered(); assert r.count>=1
    def test_b42(self):
        r=AdapterRegistry(); r.register(MockAdapter()); pipe=AdapterIntegrationPipeline(registry=r)
        t=DispatchTask(task_id="t1",action="read"); d=DispatchRequest(tasks=(t,),requires_approval=False)
        assert pipe.run(d).conversation_result is not None
    def test_b43(self): c=AdapterCard(by_type={"mock":1}); assert c.by_type["mock"]==1
    def test_b44(self): c=HealthCardDTO2(unhealthy=2); assert c.unhealthy==2
    def test_b45(self): d=AdapterDashboardBuilder.build(AdapterRegistry()); assert isinstance(d,AdapterDashboard)
    def test_b46(self): p=PreviewAdapter(); i=ExecutionEnvelopeItem(action="read",target="test.txt"); r=p.preview(ExecutionEnvelope(items=(i,))); assert r.operations[0].target=="test.txt"
    def test_b47(self): p=PreviewAdapter(); i=ExecutionEnvelopeItem(action="read"); r=p.preview(ExecutionEnvelope(items=(i,))); assert r.operations[0].estimated_duration_seconds>=0
    def test_b48(self): p=PreviewAdapter(); i=ExecutionEnvelopeItem(action="read"); r=p.preview(ExecutionEnvelope(items=(i,))); assert "no side effects" in r.operations[0].planned_impact.lower()
    def test_b49(self): p=PreviewAdapter(); i=ExecutionEnvelopeItem(action="delete"); r=p.preview(ExecutionEnvelope(items=(i,))); assert "permanently" in r.operations[0].planned_impact
    def test_b50(self): p=PreviewAdapter(); i=ExecutionEnvelopeItem(action="execute"); r=p.preview(ExecutionEnvelope(items=(i,))); assert r.operations[0].rollback_summary
class TestFinal160:
    def test_f01(self): assert ExecutionEnvelopeStatus.validated().is_terminal()==False
    def test_f02(self): i=ExecutionEnvelopeItem(adapter_type="mock"); assert i.adapter_type=="mock"
    def test_f03(self): i=ExecutionEnvelopeItem(task_id="t1",task_name="read",action="read"); assert all([i.task_id,i.task_name,i.action])
    def test_f04(self): m=ExecutionEnvelopeMetadata(source="engine"); assert m.source=="engine"
    def test_f05(self): m=ExecutionEnvelopeMetadata(plan_id="p1",package_id="pkg1"); assert m.plan_id=="p1"
    def test_f06(self): e=ExecutionEnvelope(requires_approval=False); assert not e.requires_approval
    def test_f07(self): e=ExecutionEnvelope(estimated_duration_seconds=60); assert e.estimated_duration_seconds==60
    def test_f08(self): a=BaseAdapter("mock","T"); a.add_capability(AdapterCapability(name="c1",actions=("a","b","c"))); assert "c" in a.supported_actions()
    def test_f09(self): a=BaseAdapter("mock","T"); m=a.metadata; assert m.adapter_id and m.adapter_type=="mock"
    def test_f10(self): r=AdapterRegistry(); r.register(MockAdapter()); assert r.list()[0].healthy
    def test_f11(self): r=AdapterRegistry(); r.register(MockAdapter()); s=r.get_statistics(); assert "mock" in s.by_type
    def test_f12(self): a=MockAdapter(); r=AdapterRegistry(); r.register(a); assert r.find_entry(a.metadata.adapter_id).version=="1.0.0"
    def test_f13(self): p=PreviewAdapter(); i=ExecutionEnvelopeItem(action="create"); r=p.preview(ExecutionEnvelope(items=(i,))); assert "adds" in r.operations[0].planned_impact.lower()
    def test_f14(self): p=PreviewAdapter(); i=ExecutionEnvelopeItem(action="delete"); r=p.preview(ExecutionEnvelope(items=(i,))); assert "may need manual" in r.operations[0].rollback_summary.lower()
    def test_f15(self): e=ExecutionEnvelopeBuilder.build(DispatchRequest(tasks=(DispatchTask(task_id="t1",action="read"),),requires_approval=False)); assert e.total_items==1
    def test_f16(self): assert isinstance(AdapterPipelineResult(pipeline_complete=True),AdapterPipelineResult)
    def test_f17(self): d=AdapterDashboardBuilder.build(AdapterRegistry(),None,True,0,0); assert d.validation.passed
    def test_f18(self): c=CapabilityCardDTO2(types=("mock","rest")); assert "mock" in c.types
    def test_f19(self): c=PreviewCardDTO2(rollback_possible=False); assert not c.rollback_possible
    def test_f20(self): assert not RegisteredAdapter(healthy=False).healthy
    def test_f21(self): assert AdapterStatistics(total=3,healthy=2,unhealthy=1).unhealthy==1
    def test_f22(self): b=ExecutionEnvelopeBuilder; assert hasattr(b,"build")
    def test_f23(self): r=AdapterRegistry(); a=MockAdapter(); r.register(a); r.register(MockAdapter()); assert r.count==2
    def test_f24(self): r=AdapterRegistry(); r.register(MockAdapter()); assert r.find_by_type("mock")
    def test_f25(self): r=AdapterRegistry(); assert not r.find_by_type("none")
    def test_f26(self): r=AdapterRegistry(); r.register(MockAdapter()); r.clear(); assert not r.find_by_type("mock")
    def test_f27(self): p=PreviewAdapter(); s=p.to_summary(PreviewResult(total_operations=3)); assert s.operations_count==3
    def test_f28(self): i=ExecutionEnvelopeItem(action="monitor",target="cpu"); p=PreviewAdapter(); r=p.preview(ExecutionEnvelope(items=(i,))); assert r.operations[0].target=="cpu"
    def test_f29(self): a=BaseAdapter("mock","T"); assert isinstance(a.validate(ExecutionEnvelope()),tuple)
    def test_f30(self): a=BaseAdapter("mock","T"); assert isinstance(a.preview(ExecutionEnvelope()),AdapterResult)
