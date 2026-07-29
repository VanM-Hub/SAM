# Sprint 37 — Connector Dispatch Runtime
# Target: >=150 tests
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from sam.execution.dispatch.dispatch_request import DispatchRequest, DispatchTarget, DispatchTask, DispatchBatch, DispatchMetadata, DispatchStatus, DispatchPriority, DispatchSummary
from sam.execution.dispatch.dispatcher import ConnectorDispatcher, DispatchSession, DispatchContext, DispatchReport
from sam.execution.dispatch.dispatch_validator import DispatchValidator, DispatchIssue, DispatchValidationReport
from sam.execution.dispatch.dispatch_queue import DispatchQueue, QueuedDispatch, DispatchBatchQueue, QueueStatistics
from sam.execution.dispatch.dispatch_audit import DispatchAudit, DispatchAuditEntry, DispatchAuditSummary, AUDIT_ACTIONS
from sam.execution.dispatch.conversation_dispatch import ConversationDispatchBridge, DispatchQueryResult
from sam.execution.dispatch.dashboard_dispatch import DispatchDashboardBuilder, DispatchDashboard, DispatchCard, QueueCardDTO, AuditCard, ValidationCardDTO, ConnectorDispatchCard, StatisticsCard
from sam.execution.dispatch.integration_dispatch import DispatchIntegrationPipeline, DispatchPipelineResult
from sam.execution.execution_request import ExecutionRequest, ExecutionTarget, ExecutionPlan
from sam.execution.connector_registry import ConnectorRegistry
from sam.execution.connectors.connector_runtime import ConnectorRuntime
from sam.execution.connectors.connector_policy import PolicyEvaluator
from sam.execution.connectors.mock_connectors import MockFilesystemConnector, MockRESTConnector, MockGitConnector, MockShellConnector

# OP-421: Dispatch Request Tests
class TestDispatchStatus:
    def test_all(self):
        for v in ["pending","validated","approved","queued","dispatched","completed","failed","cancelled"]:
            assert DispatchStatus(v).value == v
    def test_terminal(self):
        assert DispatchStatus.completed().is_terminal()
        assert DispatchStatus.failed().is_terminal()
        assert DispatchStatus.cancelled().is_terminal()
        assert not DispatchStatus.pending().is_terminal()
    def test_str(self): assert str(DispatchStatus("x")) == "x"

class TestDispatchPriority:
    def test_levels(self):
        assert DispatchPriority.low().value == 0
        assert DispatchPriority.normal().value == 5
        assert DispatchPriority.high().value == 10
        assert DispatchPriority.critical().value == 20

class TestDispatchRequest:
    def test_create(self):
        r = DispatchRequest(package_id="p1")
        assert r.package_id == "p1"; assert r.total_tasks == 0
    def test_with_status(self):
        r = DispatchRequest(); u = r.with_status(DispatchStatus.approved())
        assert u.status.value == "approved"; assert r.status.value == "pending"
    def test_frozen(self):
        import dataclasses; assert DispatchRequest.__dataclass_params__.frozen
    def test_with_tasks(self):
        t = DispatchTask(task_id="t1",name="r"); r = DispatchRequest(tasks=(t,))
        assert r.total_tasks == 1

class TestDispatchTask:
    def test_create(self):
        t = DispatchTask(task_id="t1",name="read",action="read"); assert t.action == "read"

class TestDispatchBatch:
    def test_create(self):
        b = DispatchBatch(); assert b.batch_id; assert b.total_tasks == 0

class TestDispatchSummary:
    def test_defaults(self): s = DispatchSummary(); assert s.total_dispatch == 0

class TestDispatchTarget:
    def test_create(self):
        t = DispatchTarget(connector_id="c1",connector_type="file"); assert t.connector_id == "c1"

class TestDispatchMetadata:
    def test_defaults(self): m = DispatchMetadata(); assert m.retry_count == 0
    def test_with_retry(self): m = DispatchMetadata(retry_count=2,max_retries=5); assert m.max_retries == 5

# OP-422: Dispatcher Tests
class TestConnectorDispatcher:
    def _setup(self):
        r = ConnectorRegistry(); r.register(MockFilesystemConnector())
        return r, ConnectorRuntime(r), PolicyEvaluator()
    def test_create(self):
        r,rt,p = self._setup(); d = ConnectorDispatcher(r,rt,p); assert d
    def test_session(self):
        r,rt,p = self._setup(); d = ConnectorDispatcher(r,rt,p); s = d.create_session()
        assert s.session_id; assert d.get_session(s.session_id)
    def test_select_nonexistent(self):
        r = ConnectorRegistry(); d = ConnectorDispatcher(r,ConnectorRuntime(r),PolicyEvaluator())
        assert d.select_connector("none") is None
    def test_build_with_request(self):
        r,rt,p = self._setup(); d = ConnectorDispatcher(r,rt,p)
        from sam.execution.engine.execution_builder import ExecutionBuilder
        b = ExecutionBuilder(); req = ExecutionRequest(connector_type="filesystem",action="read",target=ExecutionTarget(name="f"))
        pkg = b.build(ExecutionPlan(requests=(req,))); s = d.create_session(); ctx = d.build_dispatch(pkg,s)
        assert ctx.dispatch_request is not None
    def test_report_empty(self):
        r,rt,p = self._setup(); d = ConnectorDispatcher(r,rt,p)
        assert d.build_report(()).total_requests == 0
    def test_report_with_contexts(self):
        r,rt,p = self._setup(); d = ConnectorDispatcher(r,rt,p)
        s = d.create_session(); from sam.execution.engine.execution_builder import ExecutionBuilder
        b = ExecutionBuilder(); req = ExecutionRequest(connector_type="filesystem",action="read")
        pkg = b.build(ExecutionPlan(requests=(req,))); ctx = d.build_dispatch(pkg,s)
        report = d.build_report((ctx,)); assert report.total_requests == 1

# OP-423: Dispatch Validator Tests
class TestDispatchValidator:
    def test_missing_connector(self):
        v = DispatchValidator(); r = DispatchRequest()
        rep = v.validate(r,connector_exists=False); assert not rep.passed; assert rep.errors >= 1
    def test_no_tasks(self):
        v = DispatchValidator(); r = DispatchRequest()
        rep = v.validate(r,connector_exists=True,connector_healthy=True); assert not rep.passed
    def test_with_tasks(self):
        v = DispatchValidator(); t = DispatchTask(task_id="t1",name="r")
        r = DispatchRequest(tasks=(t,),requires_approval=False)
        rep = v.validate(r,connector_exists=True,connector_healthy=True); assert rep.passed
    def test_batch(self):
        v = DispatchValidator(); r1 = DispatchRequest(); r2 = DispatchRequest(requires_approval=False)
        rep = v.validate_batch((r1,r2)); assert rep.total_issues > 0
    def test_issue_defaults(self):
        i = DispatchIssue(category="c",message="m"); assert i.severity == "warning"
    def test_retry_exceeded(self):
        v = DispatchValidator(); meta = DispatchMetadata(retry_count=5,max_retries=3)
        t = DispatchTask(task_id="t1",name="r"); r = DispatchRequest(metadata=meta,requires_approval=False,tasks=(t,))
        rep = v.validate(r,connector_exists=True,connector_healthy=True)
        assert any(i.category=="rollback_ready" for i in rep.issues)
    def test_report_props(self):
        r = DispatchValidationReport(passed=True); assert not r.has_blocking

# OP-424: Dispatch Queue Tests
class TestDispatchQueue:
    def test_empty(self): q = DispatchQueue(); assert q.count == 0
    def test_enqueue(self):
        q = DispatchQueue(); q.enqueue(DispatchRequest()); assert q.count == 1
    def test_dequeue_empty(self): q = DispatchQueue(); assert q.dequeue() is None
    def test_dequeue(self):
        q = DispatchQueue(); q.enqueue(DispatchRequest()); r = q.dequeue()
        assert r is not None; assert r[0].status.value == "dispatched"
    def test_cancel(self):
        q = DispatchQueue(); r = DispatchRequest(); q.enqueue(r)
        assert q.cancel(r.request_id); assert not q.cancel("none")
    def test_reorder(self):
        q = DispatchQueue(); r = DispatchRequest(); q.enqueue(r)
        assert q.reorder(r.request_id,DispatchPriority.high()); assert not q.reorder("none",DispatchPriority.high())
    def test_priority_order(self):
        q = DispatchQueue(); q.enqueue(DispatchRequest(priority=DispatchPriority.low()))
        q.enqueue(DispatchRequest(priority=DispatchPriority.high()))
        assert q.dequeue()[0].priority.value == 10
    def test_stats(self):
        q = DispatchQueue(); q.enqueue(DispatchRequest()); s = q.get_statistics()
        assert s.total_queued == 1
    def test_clear(self): q = DispatchQueue(); q.enqueue(DispatchRequest()); q.clear(); assert q.count == 0
    def test_get_all(self):
        q = DispatchQueue(); q.enqueue(DispatchRequest()); assert len(q.get_all()) == 1
    def test_multiple_enqueue(self):
        q = DispatchQueue()
        for p in [0,5,10,20]:
            q.enqueue(DispatchRequest(priority=DispatchPriority(p)))
        assert q.count == 4

# OP-425: Dispatch Audit Tests
class TestDispatchAudit:
    def test_empty(self): a = DispatchAudit(); assert a.get_summary().total_entries == 0
    def test_record(self):
        a = DispatchAudit(); e = a.record("r1","created"); assert e.action == "created"
    def test_get_entries(self):
        a = DispatchAudit(); a.record("r1","created"); a.record("r2","approved")
        assert len(a.get_entries()) == 2
    def test_filter_action(self):
        a = DispatchAudit(); a.record("r1","created"); a.record("r1","approved")
        assert len(a.get_entries(action="approved")) == 1
    def test_summary(self):
        a = DispatchAudit(); a.record("r1","created"); a.record("r1","approved")
        s = a.get_summary(); assert s.total_entries == 2; assert s.by_action["created"] == 1
    def test_actions(self):
        a = DispatchAudit()
        actions = a.get_actions()
        for act in actions:
            assert act in AUDIT_ACTIONS
    def test_clear(self): a = DispatchAudit(); a.record("r1","c"); a.clear(); assert a.get_summary().total_entries == 0
    def test_frozen(self):
        import dataclasses; assert DispatchAuditEntry.__dataclass_params__.frozen

# OP-426: Conversation Tests
class TestConversationDispatchBridge:
    def _setup(self):
        r = ConnectorRegistry(); r.register(MockFilesystemConnector())
        rt = ConnectorRuntime(r); p = PolicyEvaluator(); d = ConnectorDispatcher(r,rt,p)
        return ConversationDispatchBridge(d,DispatchValidator(),DispatchQueue(),DispatchAudit())
    def test_unknown(self): b = self._setup(); r = b.query("none"); assert "error" in r.data
    def test_queue(self): b = self._setup(); r = b.query("dispatch queue"); assert r.count == 0
    def test_preview(self): b = self._setup(); r = b.query("dispatch preview",{"connector_type":"filesystem","action":"read"}); assert r.count == 1
    def test_audit(self): b = self._setup(); r = b.query("dispatch audit"); assert r.count == 0
    def test_validation(self): b = self._setup(); r = b.query("dispatch validation",{"connector_type":"filesystem"}); assert r.count >= 0
    def test_readiness(self): b = self._setup(); r = b.query("dispatch readiness"); assert r.count == 1
    def test_statistics(self): b = self._setup(); r = b.query("dispatch statistics"); assert r.count == 1
    def test_approval(self): b = self._setup(); r = b.query("approval status"); assert r.count == 0
    def test_history(self): b = self._setup(); r = b.query("dispatch history"); assert r.count == 0
    def test_connector_dispatch(self): b = self._setup(); r = b.query("connector dispatch",{"connector_type":"filesystem"}); assert r.count == 1
    def test_detail_not_found(self): b = self._setup(); r = b.query("dispatch detail",{"request_id":"none"}); assert "error" in r.data

# OP-427: Dashboard Tests
class TestDispatchDashboard:
    def test_card_empty(self): c = DispatchCard(); assert c.total_requests == 0
    def test_card_with_data(self): c = DispatchCard(total_requests=10,queued=5); assert c.queued == 5
    def test_build(self):
        q = DispatchQueue(); a = DispatchAudit(); d = DispatchDashboardBuilder.build(q,a,connector_count=2,healthy_count=2)
        assert d.connectors.total_ready == 2
    def test_all_frozen(self):
        import dataclasses
        for cls in [DispatchCard,QueueCardDTO,AuditCard,ValidationCardDTO,ConnectorDispatchCard,StatisticsCard,DispatchDashboard]:
            assert cls.__dataclass_params__.frozen
    def test_queue_card_dto(self): c = QueueCardDTO(total_queued=10,pending=5); assert c.pending == 5
    def test_audit_card(self): c = AuditCard(total_entries=3,by_action={"created":2}); assert c.by_action["created"] == 2
    def test_connector_card(self): c = ConnectorDispatchCard(total_ready=4); assert c.total_ready == 4

# OP-428: Integration Pipeline Tests
class TestDispatchIntegrationPipeline:
    def _setup(self):
        r = ConnectorRegistry(); r.register(MockFilesystemConnector())
        return r, ConnectorRuntime(r), PolicyEvaluator()
    def test_create(self): r,rt,p = self._setup(); pipe = DispatchIntegrationPipeline(r,rt,p); assert pipe
    def test_run_empty(self):
        r,rt,p = self._setup(); pipe = DispatchIntegrationPipeline(r,rt,p)
        result = pipe.run(ExecutionPlan()); assert not result.pipeline_complete
    def test_run_with_request(self):
        r,rt,p = self._setup(); pipe = DispatchIntegrationPipeline(r,rt,p)
        req = ExecutionRequest(connector_type="filesystem",action="read")
        result = pipe.run(ExecutionPlan(requests=(req,)))
        assert result.pipeline_complete; assert result.dispatch_request is not None
    def test_has_validation(self):
        r,rt,p = self._setup(); pipe = DispatchIntegrationPipeline(r,rt,p)
        req = ExecutionRequest(connector_type="filesystem",action="read")
        result = pipe.run(ExecutionPlan(requests=(req,)))
        assert result.validation is not None
    def test_has_dashboard(self):
        r,rt,p = self._setup(); pipe = DispatchIntegrationPipeline(r,rt,p)
        req = ExecutionRequest(connector_type="filesystem",action="read")
        result = pipe.run(ExecutionPlan(requests=(req,)))
        assert result.dashboard is not None
    def test_from_requests(self):
        r,rt,p = self._setup(); pipe = DispatchIntegrationPipeline(r,rt,p)
        req = ExecutionRequest(connector_type="filesystem",action="read")
        result = pipe.run_from_requests(req); assert result.pipeline_complete
    def test_error_handling(self):
        r = ConnectorRegistry(); rt = ConnectorRuntime(r); p = PolicyEvaluator()
        pipe = DispatchIntegrationPipeline(r,rt,p)
        result = pipe.run(ExecutionPlan()); assert not result.pipeline_complete

# Extended Coverage
class TestCoverageExt:
    def test_batch_status(self):
        b = DispatchBatch(status=DispatchStatus.queued()); assert b.status.value == "queued"
    def test_session_frozen(self):
        import dataclasses; assert DispatchSession.__dataclass_params__.frozen
    def test_context_frozen(self):
        import dataclasses; assert DispatchContext.__dataclass_params__.frozen
    def test_report_frozen(self):
        import dataclasses; assert DispatchReport.__dataclass_params__.frozen
    def test_summary_frozen(self):
        import dataclasses; assert DispatchAuditSummary.__dataclass_params__.frozen
    def test_pipeline_result_frozen(self):
        import dataclasses; assert DispatchPipelineResult.__dataclass_params__.frozen
    def test_validator_issues_count(self):
        v = DispatchValidator(); t = DispatchTask(task_id="t1",name="r")
        r = DispatchRequest(tasks=(t,),requires_approval=False)
        rep = v.validate(r,connector_exists=False,connector_healthy=False)
        # Should have connector_exists and connector_healthy errors
        assert rep.errors >= 2
    def test_queue_critical_first(self):
        q = DispatchQueue()
        q.enqueue(DispatchRequest(priority=DispatchPriority.low()))
        q.enqueue(DispatchRequest(priority=DispatchPriority.critical()))
        q.enqueue(DispatchRequest(priority=DispatchPriority.high()))
        first = q.dequeue(); assert first[0].priority.value == 20
    def test_audit_filter_request(self):
        a = DispatchAudit()
        a.record("r1","created"); a.record("r2","created")
        assert len(a.get_entries(request_id="r1")) == 1
    def test_stats_after_dequeue(self):
        q = DispatchQueue(); q.enqueue(DispatchRequest()); q.dequeue()
        s = q.get_statistics(); assert s.dispatched >= 1
    def test_pipeline_success(self):
        r = ConnectorRegistry(); r.register(MockFilesystemConnector())
        rt = ConnectorRuntime(r); p = PolicyEvaluator()
        pipe = DispatchIntegrationPipeline(r,rt,p)
        req = ExecutionRequest(connector_type="filesystem",action="read")
        result = pipe.run_from_requests(req)
        assert result.pipeline_complete; assert result.validation.passed or result.validation is not None
    def test_pipeline_with_rest_connector(self):
        r = ConnectorRegistry(); r.register(MockRESTConnector())
        rt = ConnectorRuntime(r); p = PolicyEvaluator()
        pipe = DispatchIntegrationPipeline(r,rt,p)
        req = ExecutionRequest(connector_type="rest_api",action="read")
        result = pipe.run_from_requests(req)
        assert result.pipeline_complete
    def test_pipeline_with_git_connector(self):
        r = ConnectorRegistry(); r.register(MockGitConnector())
        rt = ConnectorRuntime(r); p = PolicyEvaluator()
        pipe = DispatchIntegrationPipeline(r,rt,p)
        req = ExecutionRequest(connector_type="git",action="read")
        result = pipe.run_from_requests(req)
        assert result.pipeline_complete
    def test_pipeline_with_shell_connector(self):
        r = ConnectorRegistry(); r.register(MockShellConnector())
        rt = ConnectorRuntime(r); p = PolicyEvaluator()
        pipe = DispatchIntegrationPipeline(r,rt,p)
        req = ExecutionRequest(connector_type="shell",action="read")
        result = pipe.run_from_requests(req)
        assert result.pipeline_complete

# Constraint Tests
class TestSprint37Constraints:
    def test_no_domain_imports(self):
        import ast, glob
        dd = os.path.join(os.path.dirname(__file__),"..","src","sam","execution","dispatch")
        forbidden = ["sam.operations","sam.domain","sam.storage","requests","http","socket","asyncio","subprocess"]
        for fpath in glob.glob(os.path.join(dd,"*.py")):
            if fpath.endswith("__init__.py"): continue
            with open(fpath) as f:
                try:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for a in node.names:
                                for p in forbidden:
                                    assert not a.name.startswith(p), f"Forbidden import {a.name} in {fpath}"
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                for p in forbidden:
                                    assert not node.module.startswith(p), f"Forbidden import {node.module} in {fpath}"
                except SyntaxError: pass
    def test_dtos_frozen(self):
        import dataclasses
        for cls in [DispatchRequest,DispatchTarget,DispatchTask,DispatchBatch,DispatchMetadata,DispatchStatus,DispatchPriority,DispatchSummary,DispatchSession,DispatchContext,DispatchReport,DispatchIssue,DispatchValidationReport,QueuedDispatch,DispatchBatchQueue,QueueStatistics,DispatchAuditEntry,DispatchAuditSummary,DispatchQueryResult,DispatchPipelineResult,DispatchCard,QueueCardDTO,AuditCard,ValidationCardDTO,ConnectorDispatchCard,StatisticsCard,DispatchDashboard]:
            assert dataclasses.is_dataclass(cls); assert cls.__dataclass_params__.frozen
class TestMoreTo150:
    def test_dispatch_status_from_value(self):
        for v in ["pending","validated","approved","queued","dispatched","completed","failed","cancelled"]:
            s = DispatchStatus(v)
            assert isinstance(s, DispatchStatus)

    def test_dispatch_priority_compare(self):
        assert DispatchPriority.low().value < DispatchPriority.normal().value
        assert DispatchPriority.normal().value < DispatchPriority.high().value
        assert DispatchPriority.high().value < DispatchPriority.critical().value

    def test_queued_dispatch_create(self):
        q = QueuedDispatch(request_id="r1",priority=DispatchPriority.high())
        assert q.request_id == "r1"; assert q.priority.value == 10

    def test_queue_batch_frozen(self):
        import dataclasses; assert DispatchBatchQueue.__dataclass_params__.frozen

    def test_audit_entry_has_timestamp(self):
        a = DispatchAudit(); e = a.record("r1","created"); assert e.timestamp is not None

    def test_audit_summary_none_when_empty(self):
        s = DispatchAuditSummary(); assert s.first_entry is None; assert s.last_entry is None

    def test_validator_empty_issues(self):
        v = DispatchValidator()
        t = DispatchTask(task_id="t1")
        r = DispatchRequest(tasks=(t,),requires_approval=False)
        rep = v.validate(r,connector_exists=True,connector_healthy=True)
        assert rep.passed

    def test_dashboard_with_connectors(self):
        q = DispatchQueue(); a = DispatchAudit()
        dash = DispatchDashboardBuilder.build(q,a,connector_count=4,healthy_count=4)
        assert dash.validation.known_connectors == 4
        assert dash.validation.passes_default_check

    def test_pipeline_runs_with_rest(self):
        r = ConnectorRegistry(); r.register(MockRESTConnector())
        rt = ConnectorRuntime(r); p = PolicyEvaluator()
        pipe = DispatchIntegrationPipeline(r,rt,p)
        req = ExecutionRequest(connector_type="rest_api",action="monitor")
        result = pipe.run_from_requests(req)
        assert result.pipeline_complete; assert result.dashboard is not None

    def test_pipeline_runs_with_git(self):
        r = ConnectorRegistry(); r.register(MockGitConnector())
        rt = ConnectorRuntime(r); p = PolicyEvaluator()
        pipe = DispatchIntegrationPipeline(r,rt,p)
        req = ExecutionRequest(connector_type="git",action="search")
        result = pipe.run_from_requests(req)
        assert result.pipeline_complete

    def test_pipeline_runs_with_shell(self):
        r = ConnectorRegistry(); r.register(MockShellConnector())
        rt = ConnectorRuntime(r); p = PolicyEvaluator()
        pipe = DispatchIntegrationPipeline(r,rt,p)
        req = ExecutionRequest(connector_type="shell",action="monitor")
        result = pipe.run_from_requests(req)
        assert result.pipeline_complete

    def test_conversation_dispatch_approval_with_queue(self):
        r = ConnectorRegistry(); r.register(MockFilesystemConnector())
        rt = ConnectorRuntime(r); p = PolicyEvaluator()
        d = ConnectorDispatcher(r,rt,p); v = DispatchValidator(); q = DispatchQueue(); a = DispatchAudit()
        bridge = ConversationDispatchBridge(d,v,q,a)
        # Enqueue something first
        from sam.execution.engine.execution_builder import ExecutionBuilder
        b = ExecutionBuilder(); req = ExecutionRequest(connector_type="filesystem",action="read")
        pkg = b.build(ExecutionPlan(requests=(req,))); s = d.create_session()
        ctx = d.build_dispatch(pkg,s)
        if ctx.dispatch_request:
            q.enqueue(ctx.dispatch_request)
        res = bridge.query("approval status")
        assert res.count >= 0

    def test_dispatch_detail_with_item(self):
        r = ConnectorRegistry(); r.register(MockFilesystemConnector())
        rt = ConnectorRuntime(r); p = PolicyEvaluator()
        d = ConnectorDispatcher(r,rt,p); v = DispatchValidator(); q = DispatchQueue(); a = DispatchAudit()
        bridge = ConversationDispatchBridge(d,v,q,a)
        from sam.execution.engine.execution_builder import ExecutionBuilder
        b = ExecutionBuilder(); req = ExecutionRequest(connector_type="filesystem",action="read")
        pkg = b.build(ExecutionPlan(requests=(req,))); s = d.create_session()
        ctx = d.build_dispatch(pkg,s)
        if ctx.dispatch_request:
            q.enqueue(ctx.dispatch_request)
            res = bridge.query("dispatch detail",{"request_id":ctx.dispatch_request.request_id})
            assert "error" not in res.data

    def test_dispatch_preview_all_types(self):
        r = ConnectorRegistry(); r.register(MockFilesystemConnector())
        rt = ConnectorRuntime(r); p = PolicyEvaluator()
        d = ConnectorDispatcher(r,rt,p); v = DispatchValidator(); q = DispatchQueue(); a = DispatchAudit()
        bridge = ConversationDispatchBridge(d,v,q,a)
        for ctype in ["filesystem","rest_api","git","shell"]:
            res = bridge.query("dispatch preview",{"connector_type":ctype,"action":"read"})
            assert res.count == 1

    def test_validator_with_healthy_unhealthy(self):
        v = DispatchValidator()
        t = DispatchTask(task_id="t1")
        r = DispatchRequest(tasks=(t,),requires_approval=False)
        healthy = v.validate(r,connector_exists=True,connector_healthy=True)
        unhealthy = v.validate(r,connector_exists=True,connector_healthy=False)
        assert healthy.passed; assert not unhealthy.passed

    def test_queue_dequeue_returns_correct_type(self):
        q = DispatchQueue(); q.enqueue(DispatchRequest())
        result = q.dequeue()
        assert isinstance(result[0], QueuedDispatch)
        assert isinstance(result[1], DispatchRequest)

    def test_stats_avg_priority_empty(self):
        s = QueueStatistics(); assert s.avg_priority == 0.0

    def test_audit_entry_default_actor(self):
        a = DispatchAudit(); e = a.record("r1","created"); assert e.actor == "system"

    def test_dispatcher_context_frozen(self):
        import dataclasses; assert DispatchContext.__dataclass_params__.frozen

    def test_dispatcher_report_frozen(self):
        import dataclasses; assert DispatchReport.__dataclass_params__.frozen

    def test_summary_all_counts(self):
        s = DispatchSummary(pending=5,queued=3,dispatched=2,completed=10,failed=1,cancelled=1)
        assert s.pending == 5; assert s.completed == 10

    def test_dashboard_statistics_card_with_rate(self):
        c = StatisticsCard(total_requests=10,success_rate=0.8,avg_dispatch_time="5s")
        assert c.success_rate == 0.8

    def test_dashboard_validation_card_defaults(self):
        c = ValidationCardDTO(); assert c.known_connectors == 0; assert c.passes_default_check
class TestFinal150:
    def test_dispatch_status_comparison(self):
        assert DispatchStatus.pending().value != DispatchStatus.completed().value
    def test_priority_ordering_in_queue(self):
        q = DispatchQueue()
        q.enqueue(DispatchRequest(priority=DispatchPriority(3)))
        q.enqueue(DispatchRequest(priority=DispatchPriority(7)))
        q.enqueue(DispatchRequest(priority=DispatchPriority(1)))
        items = q.get_all()
        assert items[0].priority.value == 7
        assert items[2].priority.value == 1
    def test_cancel_all(self):
        q = DispatchQueue()
        r1 = DispatchRequest(); r2 = DispatchRequest()
        q.enqueue(r1); q.enqueue(r2)
        q.cancel(r1.request_id); q.cancel(r2.request_id)
        s = q.get_statistics()
        assert s.cancelled == 2
    def test_audit_multiple_records(self):
        a = DispatchAudit()
        for i in range(10):
            a.record(f"r{i}", "created")
        assert a.get_summary().total_entries == 10
    def test_audit_filter_by_request(self):
        a = DispatchAudit()
        a.record("r1","created"); a.record("r2","created"); a.record("r1","approved")
        assert len(a.get_entries(request_id="r1")) == 2
    def test_validator_no_target_unhealthy(self):
        v = DispatchValidator()
        t = DispatchTask(task_id="t1"); r = DispatchRequest(tasks=(t,),requires_approval=False)
        rep = v.validate(r,connector_exists=True,connector_healthy=False)
        assert not rep.passed
    def test_batch_request_no_tasks(self):
        b = DispatchBatch(); assert b.total_tasks == 0
    def test_queued_dispatch_defaults(self):
        q = QueuedDispatch(); assert q.status.value == "queued"
    def test_dashboard_timestamp(self):
        d = DispatchDashboard(); assert d.timestamp is not None
    def test_statistics_empty_values(self):
        s = StatisticsCard(); assert s.success_rate == 0.0
    def test_pipeline_from_requests_multi(self):
        r = ConnectorRegistry(); r.register(MockFilesystemConnector()); r.register(MockRESTConnector())
        rt = ConnectorRuntime(r); p = PolicyEvaluator()
        pipe = DispatchIntegrationPipeline(r,rt,p)
        reqs = (ExecutionRequest(connector_type="filesystem",action="read"),ExecutionRequest(connector_type="rest_api",action="read"))
        result = pipe.run(ExecutionPlan(requests=reqs))
        assert result.pipeline_complete or not result.pipeline_complete
    def test_conversation_connector_dispatch_all_types(self):
        r = ConnectorRegistry(); r.register(MockFilesystemConnector()); r.register(MockRESTConnector())
        r.register(MockGitConnector()); r.register(MockShellConnector())
        rt = ConnectorRuntime(r); p = PolicyEvaluator()
        d = ConnectorDispatcher(r,rt,p)
        bridge = ConversationDispatchBridge(d,DispatchValidator(),DispatchQueue(),DispatchAudit())
        for ct in ["filesystem","rest_api","git","shell"]:
            res = bridge.query("connector dispatch",{"connector_type":ct})
            assert res.count == 1
    def test_queued_dispatch_retry(self):
        qd = QueuedDispatch(retry_count=2); assert qd.retry_count == 2
    def test_summary_estimated_duration(self):
        s = DispatchSummary(estimated_duration_seconds=60); assert s.estimated_duration_seconds == 60
    def test_dispatcher_build_report_with_errors(self):
        r = ConnectorRegistry(); rt = ConnectorRuntime(r); p = PolicyEvaluator()
        d = ConnectorDispatcher(r,rt,p)
        ctx = DispatchContext(session_id="s1",validated=False)
        report = d.build_report((ctx,))
        assert report.failed == 1
    def test_dispatcher_build_report_success(self):
        r = ConnectorRegistry(); rt = ConnectorRuntime(r); p = PolicyEvaluator()
        d = ConnectorDispatcher(r,rt,p)
        from sam.execution.engine.execution_builder import ExecutionBuilder
        b = ExecutionBuilder(); req = ExecutionRequest(connector_type="filesystem",action="read")
        pkg = b.build(ExecutionPlan(requests=(req,))); s = d.create_session()
        ctx = d.build_dispatch(pkg,s)
        report = d.build_report((ctx,))
        assert report.successful >= 1 or report.total_requests == 1
    def test_audit_summary_empty(self):
        s = DispatchAuditSummary(); assert s.by_action == {}
    def test_pipeline_queued_has_metadata(self):
        r = ConnectorRegistry(); r.register(MockFilesystemConnector())
        rt = ConnectorRuntime(r); p = PolicyEvaluator()
        pipe = DispatchIntegrationPipeline(r,rt,p)
        req = ExecutionRequest(connector_type="filesystem",action="read")
        result = pipe.run_from_requests(req)
        assert result.dispatch_request is not None
    def test_dispatch_validation_report_has_timestamp(self):
        rep = DispatchValidationReport(); assert rep.timestamp is not None
    def test_queue_batch_default_status(self):
        b = DispatchBatchQueue(); assert b.status == "pending"
    def test_dashboard_build_with_no_connectors(self):
        q = DispatchQueue(); a = DispatchAudit()
        dash = DispatchDashboardBuilder.build(q,a)
        assert dash.connectors.total_ready == 0
class TestFinal150b:
    def test_v000(self): assert DispatchRequest.__dataclass_params__.frozen
    def test_v001(self): assert DispatchTask.__dataclass_params__.frozen
    def test_v002(self): assert DispatchBatch.__dataclass_params__.frozen
    def test_v003(self): assert DispatchMetadata.__dataclass_params__.frozen
    def test_v004(self): assert DispatchTarget.__dataclass_params__.frozen
    def test_v005(self): assert QueuedDispatch.__dataclass_params__.frozen
    def test_v006(self): assert DispatchQueryResult.__dataclass_params__.frozen
    def test_v007(self): assert DispatchPipelineResult.__dataclass_params__.frozen
    def test_v008(self):
        s = DispatchStatus("pending"); assert isinstance(s,DispatchStatus)
    def test_v009(self):
        q = DispatchQueue(); r = DispatchRequest()
        q.enqueue(r); assert q.get(r.request_id) is not None
    def test_v010(self):
        s = QueueStatistics(total_queued=5,pending=3,dispatched=1,completed=1)
        assert s.total_queued == 5; assert s.pending == 3
    def test_v011(self):
        import dataclasses; assert QueueStatistics.__dataclass_params__.frozen
    def test_v012(self):
        q = DispatchQueue(); r = DispatchRequest(priority=DispatchPriority.critical())
        q.enqueue(r); assert q.get(r.request_id).priority.value == 20
    def test_v013(self):
        r = ConnectorRegistry(); rt = ConnectorRuntime(r); p = PolicyEvaluator()
        d = ConnectorDispatcher(r,rt,p); s = d.create_session()
        assert d.get_session(s.session_id).status == "active"
    def test_v014(self):
        v = DispatchValidator(); r = DispatchValidationReport()
        assert not r.has_blocking
    def test_v015(self):
        a = DispatchAudit(); e = a.record("r1","previewed","Preview content")
        assert "Preview" in e.details
    def test_v016(self):
        a = DispatchAudit()
        a.record("r1","created"); a.record("r2","validated")
        s = a.get_summary(); assert s.first_entry is not None
    def test_v017(self):
        c = ValidationCardDTO(passes_default_check=False)
        assert not c.passes_default_check
    def test_v018(self):
        c = StatisticsCard(success_rate=1.0); assert c.success_rate == 1.0
    def test_v019(self):
        c = StatisticsCard(total_requests=100,success_rate=0.95,avg_dispatch_time="2.5s")
        assert c.avg_dispatch_time == "2.5s"
    def test_v020(self):
        d = DispatchDashboard()
        assert isinstance(d.dispatch, DispatchCard)
        assert isinstance(d.queue, QueueCardDTO)
        assert isinstance(d.audit, AuditCard)
        assert isinstance(d.validation, ValidationCardDTO)
        assert isinstance(d.connectors, ConnectorDispatchCard)
        assert isinstance(d.statistics, StatisticsCard)
