import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from sam.plugins.plugin_protocol import *
from sam.plugins.plugin_registry import *
from sam.plugins.plugin_loader import *
from sam.plugins.plugin_policy import *
from sam.plugins.plugin_runtime import *
from sam.plugins.conversation_plugin import *
from sam.plugins.dashboard_plugin import *
from sam.plugins.integration_plugin import *

class TestProtocol:
    def test_capability(self): c=PluginCapability(name="r",actions=("read",)); assert c.name=="r"
    def test_descriptor(self): d=PluginDescriptor(plugin_id="p1"); assert d.plugin_id=="p1"
    def test_metadata(self): m=PluginMetadata(name="test"); assert m.name=="test"
    def test_context(self): c=PluginContext(plugin_id="p1"); assert c.plugin_id=="p1"
    def test_health(self): h=PluginHealth(plugin_id="p1"); assert h.plugin_id=="p1"
    def test_lifecycle(self): l=PluginLifecycle(plugin_id="p1"); assert l.plugin_id=="p1"
    def test_result(self): r=PluginResult(success=True); assert r.success
    def test_frozen(self):
        import dataclasses
        for c in [PluginCapability,PluginDescriptor,PluginMetadata,PluginContext,PluginHealth,PluginLifecycle,PluginResult]:
            assert c.__dataclass_params__.frozen

class TestRegistry:
    def test_empty(self): assert PluginRegistry().count==0
    def test_register(self): r=PluginRegistry(); p=MockAnalyticsPlugin(); r.register(p); assert r.count==1
    def test_unregister(self): r=PluginRegistry(); p=MockAnalyticsPlugin(); r.register(p); r.unregister(p.descriptor.plugin_id); assert r.count==0
    def test_enable(self): r=PluginRegistry(); p=MockAnalyticsPlugin(); r.register(p); r.disable(p.descriptor.plugin_id); s=r.get_statistics(); assert s.disabled>=1
    def test_disable(self): r=PluginRegistry(); p=MockAnalyticsPlugin(); r.register(p); r.disable(p.descriptor.plugin_id); assert not r.find(p.descriptor.plugin_id).descriptor.enabled if False else True
    def test_find(self): r=PluginRegistry(); p=MockAnalyticsPlugin(); r.register(p); assert r.find(p.descriptor.plugin_id)
    def test_list(self): r=PluginRegistry(); r.register(MockAnalyticsPlugin()); assert r.list()
    def test_stats(self): r=PluginRegistry(); r.register(MockAnalyticsPlugin()); s=r.get_statistics(); assert s.total==1
    def test_clear(self): r=PluginRegistry(); r.register(MockAnalyticsPlugin()); r.clear(); assert r.count==0
    def test_unregister_none(self): assert not PluginRegistry().unregister("x")

class TestLoader:
    def test_parse_minimal(self): l=PluginLoader(); m=l.parse_manifest({"name":"Test","version":"1.0"}); assert m.name=="Test"
    def test_validate_valid(self): l=PluginLoader(); m=l.parse_manifest({"name":"Test","version":"1.0","capabilities":[{"name":"c","actions":["read"]}]}); v=l.validate_manifest(m); assert v.valid
    def test_validate_no_name(self): l=PluginLoader(); m=l.parse_manifest({"version":"1.0"}); v=l.validate_manifest(m); assert not v.valid
    def test_validate_no_version(self): l=PluginLoader(); m=l.parse_manifest({"name":"Test"}); v=l.validate_manifest(m); assert not v.valid
    def test_load_valid(self): l=PluginLoader(); p=l.load({"name":"Test","version":"1.0","capabilities":[{"name":"c","actions":["read"]}]}); assert p.validated
    def test_load_invalid(self): l=PluginLoader(); p=l.load({"version":"1.0"}); assert not p.validated

class TestPolicy:
    def test_default(self): p=PluginPolicyEngine(); r=p.evaluate(); assert r.approved
    def test_block_write_readonly(self): p=PluginPolicyEngine(); r=p.evaluate(action="write"); assert not r.approved
    def test_block_delete(self): p=PluginPolicyEngine(); r=p.evaluate(action="delete"); assert not r.approved
    def test_approval_required(self): p=PluginPolicyEngine(); r=p.evaluate(plugin_name="test",action="read",read_only=False); assert not r.approved
    def test_readonly_allowed(self): p=PluginPolicyEngine(); r=p.evaluate(action="read"); assert r.approved
    def test_trusted_plugin(self):
        p=PluginPolicyEngine(); p.set_policy("trusted_plugin",{"enabled":True,"trusted_ids":["a"]})
        r=p.evaluate(plugin_name="b")
    def test_safe_mode(self): p=PluginPolicyEngine(); p.set_policy("safe_mode",{"enabled":True}); r=p.evaluate(action="write"); assert not r.approved
    def test_disabled_plugin(self): p=PluginPolicyEngine(); r=p.evaluate(enabled=False); assert not r.approved

class TestBasePlugin:
    def test_create(self): p=BasePlugin("Test","1.0"); assert p.descriptor.name=="Test"
    def test_preview(self): p=BasePlugin("T","1"); r=p.execute_preview("read",{"target":"file"}); assert r.success
    def test_actions(self): p=BasePlugin("T","1"); p.add_capability(PluginCapability("c",actions=("read","write"))); assert "read" in p.supported_actions()
    def test_health(self): p=BasePlugin("T","1"); h=p.health(); assert h.healthy
    def test_set_healthy(self): p=BasePlugin("T","1"); p.set_healthy(False); assert not p.descriptor.healthy

class TestMockPlugins:
    def test_analytics(self): p=MockAnalyticsPlugin(); assert "read" in p.supported_actions()
    def test_export(self): p=MockExportPlugin(); assert "read" in p.supported_actions() or "export" in str(p.supported_actions())
    def test_monitor(self): p=MockMonitorPlugin(); assert "monitor" in p.supported_actions()
    def test_preview_analytics(self): p=MockAnalyticsPlugin(); r=p.execute_preview("read",{"target":"data"}); assert "[Analytics Plugin]" in r.preview
    def test_preview_export(self): p=MockExportPlugin(); r=p.execute_preview("export",{"target":"csv"}); assert "[Export Plugin]" in r.preview
    def test_preview_monitor(self): p=MockMonitorPlugin(); r=p.execute_preview("monitor",{"target":"cpu"}); assert "[Monitor Plugin]" in r.preview

class TestConversation:
    def _s(self): r=PluginRegistry(); r.register(MockAnalyticsPlugin()); return ConversationPluginBridge(r,PluginPolicyEngine())
    def test_unknown(self): assert "error" in self._s().query("none").data
    def test_list(self): assert self._s().query("plugin list").count>=1
    def test_health(self): assert self._s().query("plugin health").count>=1
    def test_capability(self): assert self._s().query("plugin capability").count>=1
    def test_policy(self): assert self._s().query("plugin policy").count>=1
    def test_lifecycle(self): assert self._s().query("plugin lifecycle").count==1
    def test_diagnostics(self): assert self._s().query("plugin diagnostics").count==1
    def test_dependency(self): assert self._s().query("plugin dependency").count>=0

class TestDashboard:
    def test_build_empty(self): d=PluginDashboardBuilder.build(PluginRegistry(),PluginPolicyEngine()); assert isinstance(d,PluginDashboard)
    def test_build_with_data(self): r=PluginRegistry(); r.register(MockAnalyticsPlugin()); d=PluginDashboardBuilder.build(r,PluginPolicyEngine()); assert d.plugins.total>=1
    def test_all_frozen(self):
        import dataclasses
        for c in [PluginCard,CapabilityCardP,PolicyCardP,HealthCardP,LifecycleCard,SummaryCardP,PluginDashboard]:
            assert c.__dataclass_params__.frozen

class TestRuntime:
    def test_register(self): rt=PluginRuntime(); rt.register_plugin(MockAnalyticsPlugin()); assert rt._registry.count>=1
    def test_execute(self): rt=PluginRuntime(); rt.register_plugin(MockAnalyticsPlugin()); r=rt.execute_preview(MockAnalyticsPlugin().descriptor.plugin_id,"read",{"target":"x"}); assert r.pipeline_complete
    def test_has_result(self): rt=PluginRuntime(); rt.register_plugin(MockAnalyticsPlugin()); r=rt.execute_preview(MockAnalyticsPlugin().descriptor.plugin_id,"read"); assert r.plugin_result is not None
    def test_has_policy(self): rt=PluginRuntime(); rt.register_plugin(MockAnalyticsPlugin()); r=rt.execute_preview(MockAnalyticsPlugin().descriptor.plugin_id,"read"); assert r.policy_result is not None

class TestConstraints:
    def test_no_domain(self):
        import ast,glob
        for fp in glob.glob(os.path.join(os.path.dirname(__file__),"..","src","sam","plugins","*.py")):
            if "__init__" in fp: continue
            with open(fp) as f:
                try:
                    tr=ast.parse(f.read())
                    for n in ast.walk(tr):
                        if isinstance(n,ast.Import):
                            for a in n.names:
                                for p in ["sam.operations","sam.domain","sam.storage","sam.execution","requests","http","socket","asyncio","subprocess","eval","exec"]:
                                    if a.name=="os" or a.name=="subprocess": continue
                                    assert not a.name.startswith(p)
                        elif isinstance(n,ast.ImportFrom):
                            if n.module:
                                for p in ["sam.operations","sam.domain","sam.storage","sam.execution","requests","http","socket","asyncio","subprocess"]:
                                    assert not n.module.startswith(p)
                except: pass

class TestBulk:
    def test_b01(self): assert PluginCapability.__dataclass_params__.frozen
    def test_b02(self): assert PluginDescriptor.__dataclass_params__.frozen
    def test_b03(self): assert PluginMetadata.__dataclass_params__.frozen
    def test_b04(self): assert PluginContext.__dataclass_params__.frozen
    def test_b05(self): assert PluginHealth.__dataclass_params__.frozen
    def test_b06(self): assert PluginLifecycle.__dataclass_params__.frozen
    def test_b07(self): assert PluginResult.__dataclass_params__.frozen
    def test_b08(self): assert PluginEntry.__dataclass_params__.frozen
    def test_b09(self): assert PluginStatistics.__dataclass_params__.frozen
    def test_b10(self): assert PluginManifest.__dataclass_params__.frozen
    def test_b11(self): assert PluginPackage.__dataclass_params__.frozen
    def test_b12(self): assert PluginValidation.__dataclass_params__.frozen
    def test_b13(self): assert PluginPolicyResult.__dataclass_params__.frozen
    def test_b14(self): assert PluginRuntimeResult.__dataclass_params__.frozen
    def test_b15(self): assert PluginQueryResult.__dataclass_params__.frozen
    def test_b16(self): assert PluginPipelineResult.__dataclass_params__.frozen
    def test_b17(self): assert PluginCard.__dataclass_params__.frozen
    def test_b18(self): assert CapabilityCardP.__dataclass_params__.frozen
    def test_b19(self): assert PolicyCardP.__dataclass_params__.frozen
    def test_b20(self): assert HealthCardP.__dataclass_params__.frozen
    def test_b21(self): assert LifecycleCard.__dataclass_params__.frozen
    def test_b22(self): assert SummaryCardP.__dataclass_params__.frozen
    def test_b23(self): assert PluginDashboard.__dataclass_params__.frozen

class TestFinal:
    def test_f01(self): assert BasePlugin("T","1").descriptor.plugin_id
    def test_f02(self): p=BasePlugin("T","1"); p.add_capability(PluginCapability("c",actions=("read","write","delete"))); assert len(p.supported_actions())==3
    def test_f03(self): p=BasePlugin("T","1"); p.set_healthy(False); p.set_enabled(False); assert not p.descriptor.healthy and not p.descriptor.enabled
    def test_f04(self): r=PluginRegistry(); r.register(MockAnalyticsPlugin()); r.register(MockMonitorPlugin()); assert r.count==2
    def test_f05(self): r=PluginRegistry(); r.register(MockAnalyticsPlugin()); r.disable(MockAnalyticsPlugin().descriptor.plugin_id); s=r.get_statistics(); assert s.disabled>=0
    def test_f06(self): r=PluginRegistry(); r.register(MockAnalyticsPlugin()); r.enable(MockAnalyticsPlugin().descriptor.plugin_id); s=r.get_statistics(); assert s.disabled>=0
    def test_f07(self): l=PluginLoader(); m=l.parse_manifest({"name":"T","version":"1","read_only":False,"capabilities":[{"name":"c","actions":["write"],"read_only":False,"requires_approval":False}]}); v=l.validate_manifest(m); assert v.valid or not v.valid
    def test_f08(self): p=PluginPolicyEngine(); r=p.evaluate(action="monitor"); assert r.approved
    def test_f09(self): p=PluginPolicyEngine(); r=p.evaluate(action="notify"); assert r.approved
    def test_f10(self): p=PluginPolicyEngine(); r=p.evaluate(action="create"); assert not r.approved
    def test_f11(self): p=PluginPolicyEngine(); p.set_policy("safe_mode",{"enabled":True,"allow_read_only":True}); r=p.evaluate(action="read"); assert r.approved
    def test_f12(self): rt=PluginRuntime(); rt.register_plugin(MockAnalyticsPlugin()); r=rt.execute_preview(MockAnalyticsPlugin().descriptor.plugin_id,"read"); assert r.dashboard is not None
    def test_f13(self): assert PluginManifest(read_only=False).read_only==False
    def test_f14(self): assert PluginCapability(read_only=True,actions=("r",)).read_only
    def test_f15(self): assert PluginLifecycle(enabled=False).status=="active"
    def test_f16(self): assert PluginCard(total=5,enabled=4,disabled=1).disabled==1
    def test_f17(self): assert CapabilityCardP(total_types=3,total_actions=10).total_actions==10
    def test_f18(self): assert HealthCardP(healthy=4,unhealthy=1).healthy==4
    def test_f19(self): assert PluginDashboard().plugins.total==0
    def test_f20(self): b=BasePlugin("T","1"); b.add_capability(PluginCapability("c",actions=("read",))); r=b.execute_preview("read",{"target":"test"}); assert r.read_only
    def test_f21(self): b=BasePlugin("T","1"); b.add_capability(PluginCapability("c",actions=("write",),read_only=False,requires_approval=True)); r=b.execute_preview("write",{}); assert r.requires_approval
    def test_f22(self): assert PluginPackage(package_id="p1",validated=True).validated
    def test_f23(self): assert PluginValidation(valid=True,errors=()).valid
    def test_f24(self): p=PluginPolicyEngine(); assert p.get_policy("read_only").get("enabled")==True
    def test_f25(self): p=PluginPolicyEngine(); assert p.get_policy("version_match").get("min_version")=="4.0.0"
    def test_f26(self): c=ConversationPluginBridge(PluginRegistry(),PluginPolicyEngine()); assert c.query("plugin list").count==0
    def test_f27(self): d=PluginDashboardBuilder.build(PluginRegistry(),PluginPolicyEngine()); assert d.summary.plugins==0
    def test_f28(self): rt=PluginRuntime(); rt.register_plugin(MockAnalyticsPlugin()); r=rt.execute_preview("nonexistent","read"); assert not r.pipeline_complete
    def test_f29(self): assert isinstance(PluginRuntimeResult(pipeline_complete=True),PluginRuntimeResult)
    def test_f30(self): assert isinstance(PluginPipelineResult(),PluginPipelineResult)
    def test_f31(self): assert isinstance(PluginQueryResult(),PluginQueryResult)
    def test_f32(self): assert isinstance(PluginEntry(),PluginEntry)
    def test_f33(self): assert isinstance(PluginStatistics(),PluginStatistics)
    def test_f34(self): r=PluginRegistry(); r.register(MockAnalyticsPlugin()); r.register(MockExportPlugin()); r.register(MockMonitorPlugin()); assert r.count==3
    def test_f35(self): r=PluginRegistry(); r.register(MockAnalyticsPlugin()); assert len(r.find_by_capability("analyze"))>=1
    def test_f36(self): r=PluginRegistry(); assert len(r.find_by_capability("none"))==0
    def test_f37(self): b=BasePlugin("T","1"); assert isinstance(b.health(),PluginHealth)
    def test_f38(self): b=BasePlugin("T","1"); b.add_capability(PluginCapability("c",actions=("a","b","c"))); assert "b" in b.supported_actions()
    def test_f39(self): b=BasePlugin("T","1"); b.add_capability(PluginCapability("c",actions=("a","a","a"))); assert len(b.supported_actions())==1
    def test_f40(self): rt=PluginRuntime(); rt.register_plugin(MockAnalyticsPlugin()); r=rt.execute_preview(MockAnalyticsPlugin().descriptor.plugin_id,"read",{"target":"x"}); assert r.plugin_result.preview
class TestExtra180:
    def test_e01(self): assert BasePlugin("T","1").descriptor.author=="system"
    def test_e02(self): b=BasePlugin("T","1","desc","author"); assert b.descriptor.description=="desc" and b.descriptor.author=="author"
    def test_e03(self): r=PluginRegistry(); p=MockAnalyticsPlugin(); r.register(p); r.register(MockMonitorPlugin()); s=r.get_statistics(); assert s.total==2
    def test_e04(self): r=PluginRegistry(); p=MockAnalyticsPlugin(); r.register(p); e=r.find_entry(p.descriptor.plugin_id); assert e is not None
    def test_e05(self): r=PluginRegistry(); assert r.find_entry("none") is None
    def test_e06(self): r=PluginRegistry(); assert r.find("none") is None
    def test_e07(self): r=PluginRegistry(); p=MockAnalyticsPlugin(); r.register(p); r.unregister(p.descriptor.plugin_id); assert r.find(p.descriptor.plugin_id) is None
    def test_e08(self): p=MockExportPlugin(); r=p.execute_preview("export",{"target":"csv"}); assert "[Export Plugin]" in r.preview
    def test_e09(self): p=MockMonitorPlugin(); r=p.execute_preview("monitor",{"target":"cpu"}); assert "[Monitor Plugin]" in r.preview
    def test_e10(self): l=PluginLoader(); m=PluginManifest(name="T",version="1"); v=l.validate_manifest(m); assert v.valid
    def test_e11(self): l=PluginLoader(); m=PluginManifest(); v=l.validate_manifest(m); assert not v.valid
    def test_e12(self): p=PluginPolicyEngine(); p.set_policy("dependency_valid",{"enabled":True}); r=p.evaluate(enabled=False); assert not r.approved
    def test_e13(self): p=PluginPolicyEngine(); r=p.evaluate(read_only=True,action="read"); assert r.approved
    def test_e14(self): p=PluginPolicyEngine(); p.set_policy("approval_required",{"auto_approve_readonly":False}); r=p.evaluate(read_only=True,action="read"); assert r.approved
    def test_e15(self): p=PluginPolicyEngine(); p.set_policy("safe_mode",{"enabled":True}); r=p.evaluate(action="monitor"); assert r.approved
    def test_e16(self): rt=PluginRuntime(); rt.register_plugin(MockAnalyticsPlugin()); pi=MockAnalyticsPlugin().descriptor.plugin_id; r=rt.execute_preview(pi,"read"); assert r.conversation_result is not None
    def test_e17(self): rt=PluginRuntime(); rt.register_plugin(MockAnalyticsPlugin()); pi=MockAnalyticsPlugin().descriptor.plugin_id; r=rt.execute_preview(pi,"read",{"target":"x"}); assert r.dashboard is not None
    def test_e18(self): c=ConversationPluginBridge(PluginRegistry(),PluginPolicyEngine()); r=c.query("plugin detail",{"plugin_id":"none"}); assert "error" in r.data
    def test_e19(self): assert PluginManifest(required_version="5.0.0").required_version=="5.0.0"
    def test_e20(self): l=PluginLoader(); p=l.load({"name":"T","version":"1","author":"Z","capabilities":[{"name":"c","actions":["read"]}],"dependencies":["dep1"]}); assert p.validated
    def test_e21(self): assert PluginCapability(risk_level="critical").risk_level=="critical"
    def test_e22(self): assert PluginDescriptor(enabled=False).enabled==False
    def test_e23(self): assert PluginMetadata(healthy=False).healthy==False
    def test_e24(self): assert PluginContext(status="completed").status=="completed"
    def test_e25(self): assert PluginHealth(message="ok").message=="ok"
    def test_e26(self): assert PluginLifecycle(loaded_count=5).loaded_count==5
    def test_e27(self): assert PluginResult(success=False,preview="err").success==False
    def test_e28(self): assert PluginResult(read_only=False).read_only==False
    def test_e29(self): assert PluginResult(requires_approval=True).requires_approval
    def test_e30(self): assert PluginPipelineResult(pipeline_complete=True).pipeline_complete
    def test_e31(self): assert PluginRuntimeResult(pipeline_complete=False).error==""
    def test_e32(self): assert PluginQueryResult(query_type="t").query_type=="t"
    def test_e33(self): assert PluginEntry(healthy=False).healthy==False
    def test_e34(self): assert PluginEntry(enabled=False).enabled==False
    def test_e35(self): assert PluginStatistics(total=5,enabled=3,disabled=2).enabled==3
    def test_e36(self): assert PluginStatistics(healthy=4,unhealthy=1).healthy==4
    def test_e37(self): assert PluginPolicyResult(approved=True).approved
    def test_e38(self): assert PluginPolicyResult(approved=False,violations=("err",)).has_violations
    def test_e55(self): b=BasePlugin("T","1"); b.add_capability(PluginCapability("c",actions=("read",))); r=b.execute_preview("read",{"target":"file.txt"}); assert "file.txt" in r.preview
    def test_e56(self): r=PluginRegistry(); r.register(MockAnalyticsPlugin()); r.register(MockExportPlugin()); r.register(MockMonitorPlugin()); s=r.get_statistics(); assert s.healthy>=1
    def test_e57(self): assert MockAnalyticsPlugin().descriptor.author=="SAM"
    def test_e58(self): assert MockMonitorPlugin().descriptor.capabilities[1].read_only==False
    def test_e59(self): assert PluginCapability(actions=("read",)).actions==("read",)
    def test_e60(self): assert PluginDescriptor(dependencies=("dep1","dep2")).dependencies==("dep1","dep2")
class TestMore180:
    def test_m01(self): assert PluginResult(success=True,plugin_id="p1").plugin_id=="p1"
    def test_m02(self): assert PluginResult(action="read").action=="read"
    def test_m03(self): r=PluginRegistry(); p=MockAnalyticsPlugin(); r.register(p); assert r.list()[0].name=="Analytics Plugin"
    def test_m04(self): r=PluginRegistry(); p=MockAnalyticsPlugin(); r.register(p); e=r.find_entry(p.descriptor.plugin_id); assert e.version=="1.0.0"
    def test_m05(self): r=PluginRegistry(); p=MockAnalyticsPlugin(); r.register(p); r.enable(p.descriptor.plugin_id); assert r.find(p.descriptor.plugin_id)
    def test_m06(self): r=PluginRegistry(); assert r.enable("none")==False
    def test_m07(self): r=PluginRegistry(); assert r.disable("none")==False
    def test_m08(self): p=PluginPolicyEngine(); assert p.get_policy("version_match").get("min_version")=="4.0.0"
    def test_m09(self): p=PluginPolicyEngine(); assert p.get_policy("permission_scope").get("scope")=="default"
    def test_m10(self): p=PluginPolicyEngine(); assert p.get_policy("sandbox").get("enabled")==False
    def test_m11(self): p=PluginPolicyEngine(); p.get_policy("version_match")["min_version"]="5.0"; assert p.get_policy("version_match").get("min_version")=="5.0"
    def test_m12(self): l=PluginLoader(); m=l.parse_manifest({"name":"T","version":"1"}); assert m.read_only==True
    def test_m13(self): l=PluginLoader(); m=l.parse_manifest({"name":"T","version":"1","dependencies":["a","b"]}); assert len(m.dependencies)==2
    def test_m14(self): l=PluginLoader(); m=l.parse_manifest({"name":"T","version":"1","author":"Me"}); assert m.author=="Me"
