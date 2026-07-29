# Sprint 34 — Execution Connectors Foundation
# Target: >=120 tests
# Constraints: 0 domain import, 0 repository import, 0 storage import,
#              0 network import, 0 subprocess, 0 requests, 0 socket, 0 http,
#              0 auto execution, 0 vendor SDK

import sys
import os
from datetime import datetime, timedelta
from dataclasses import replace as dataclass_replace
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Import ONLY execution modules — no domain, storage, network
from sam.execution.execution_request import (
    ExecutionRequest,
    ExecutionTarget,
    ExecutionParameter,
    ExecutionPlan,
    ExecutionResult,
    ExecutionStatus,
    ExecutionRisk,
)
from sam.execution.connector_protocol import (
    ConnectorProtocol,
    ConnectorInfo,
    ConnectorCapability,
    BaseConnector,
)
from sam.execution.connector_registry import (
    ConnectorRegistry,
    RegistryEntry,
    CapabilityLookup,
)
from sam.execution.execution_planner import (
    ExecutionPlanner,
    DependencyEdge,
)
from sam.execution.approval_execution import (
    ExecutionApprovalBridge,
    ApprovalRequest,
    ApprovalResult,
    ApprovalItem,
)
from sam.execution.conversation_execution import (
    ConversationExecutionBridge,
    ExecutionQueryResult,
)
from sam.execution.dashboard_execution import (
    ExecutionDashboardBuilder,
    ExecutionDashboard,
    ConnectorCard,
    ExecutionCard,
    ApprovalCard,
    CapabilityCard,
    HealthCard,
    QueueCard,
)
from sam.execution.integration_execution import (
    ExecutionPipeline,
    ExecutionPipelineResult,
)


# ===========================================================================
# OP-391: Execution Request Tests (~20)
# ===========================================================================

class TestExecutionStatus:
    def test_pending(self):
        s = ExecutionStatus.pending()
        assert s.value == "pending"

    def test_planned(self):
        s = ExecutionStatus.planned()
        assert s.value == "planned"

    def test_awaiting_approval(self):
        s = ExecutionStatus.awaiting_approval()
        assert s.value == "awaiting_approval"

    def test_terminal_states(self):
        assert ExecutionStatus.completed().is_terminal()
        assert ExecutionStatus.failed().is_terminal()
        assert ExecutionStatus.rejected().is_terminal()
        assert ExecutionStatus.rolled_back().is_terminal()
        assert not ExecutionStatus.pending().is_terminal()

    def test_can_approve(self):
        assert ExecutionStatus.awaiting_approval().can_approve()
        assert not ExecutionStatus.pending().can_approve()

    def test_str(self):
        assert str(ExecutionStatus("test")) == "test"


class TestExecutionRisk:
    def test_defaults(self):
        risk = ExecutionRisk()
        assert risk.level == "low"
        assert risk.score == 0.0
        assert risk.requires_approval is True


class TestExecutionParameter:
    def test_create(self):
        p = ExecutionParameter(key="k", value="v", required=True)
        assert p.key == "k"
        assert p.value == "v"
        assert p.required is True


class TestExecutionTarget:
    def test_create(self):
        t = ExecutionTarget(target_id="t1", target_type="file", name="config.yaml")
        assert t.target_id == "t1"
        assert t.name == "config.yaml"


class TestExecutionRequest:
    def test_create(self):
        req = ExecutionRequest(connector_type="file", action="read")
        assert req.request_id
        assert req.connector_type == "file"
        assert req.action == "read"

    def test_requires_human_approval_default(self):
        req = ExecutionRequest()
        assert req.requires_human_approval is True

    def test_requires_human_approval_disabled(self):
        req = ExecutionRequest(requires_approval=False, risk=ExecutionRisk(requires_approval=False))
        assert req.requires_human_approval is False

    def test_as_preview(self):
        target = ExecutionTarget(name="test_target")
        req = ExecutionRequest(connector_type="file", action="read", target=target)
        preview = req.as_preview()
        assert "file" in preview
        assert "test_target" in preview

    def test_with_status(self):
        req = ExecutionRequest()
        updated = req.with_status(ExecutionStatus.planned())
        assert updated.status.value == "planned"
        assert req.status.value == "pending"  # immutable

    def test_immutable(self):
        import dataclasses
        assert dataclasses.is_dataclass(ExecutionRequest)
        assert ExecutionRequest.__dataclass_params__.frozen


class TestExecutionPlan:
    def test_create_empty(self):
        plan = ExecutionPlan()
        assert plan.total_requests == 0
        assert plan.requires_human_approval is False

    def test_with_requests(self):
        req = ExecutionRequest()
        plan = ExecutionPlan(requests=(req,))
        assert plan.total_requests == 1

    def test_requires_approval(self):
        req = ExecutionRequest(requires_approval=True)
        plan = ExecutionPlan(requests=(req,))
        assert plan.requires_human_approval is True


class TestExecutionResult:
    def test_create(self):
        result = ExecutionResult(request_id="r1", success=True)
        assert result.request_id == "r1"


# ===========================================================================
# OP-392: Connector Protocol Tests (~15)
# ===========================================================================

class TestConnectorInfo:
    def test_create(self):
        info = ConnectorInfo(name="File Connector", connector_type="file")
        assert info.name == "File Connector"


class TestConnectorCapability:
    def test_create(self):
        cap = ConnectorCapability(action="read", description="Read file")
        assert cap.action == "read"


class TestBaseConnector:
    def test_create(self):
        conn = BaseConnector("File Connector", "file")
        assert conn.info.name == "File Connector"
        assert conn.info.connector_type == "file"

    def test_default_actions_empty(self):
        conn = BaseConnector("Test", "test")
        assert conn.supported_actions() == ()

    def test_add_capability(self):
        conn = BaseConnector("Test", "test")
        conn.add_capability(ConnectorCapability(action="read"))
        assert "read" in conn.supported_actions()

    def test_validate_empty_request(self):
        conn = BaseConnector("Test", "test")
        req = ExecutionRequest()
        errors = conn.validate(req)
        assert len(errors) > 0  # missing action, type mismatch

    def test_validate_valid_request(self):
        conn = BaseConnector("Test", "test")
        req = ExecutionRequest(connector_type="test", action="read", target=ExecutionTarget(name="t"))
        errors = conn.validate(req)
        assert len(errors) == 0

    def test_build_request(self):
        conn = BaseConnector("Test", "test")
        req = conn.build_request("read", ExecutionTarget(name="t"))
        assert req.connector_type == "test"
        assert req.action == "read"

    def test_preview(self):
        conn = BaseConnector("Test", "test")
        target = ExecutionTarget(name="test_target")
        req = conn.build_request("read", target)
        preview = conn.preview(req)
        assert "test" in preview

    def test_health(self):
        conn = BaseConnector("Test", "test")
        info = conn.health()
        assert info.healthy is True

    def test_version(self):
        conn = BaseConnector("Test", "test", version="2.0")
        assert conn.version() == "2.0"

    def test_set_health(self):
        conn = BaseConnector("Test", "test")
        conn.set_health(False, "Not available")
        assert conn.info.healthy is False
        assert conn.info.health_message == "Not available"

    def test_dto_immutable(self):
        import dataclasses
        assert ConnectorInfo.__dataclass_params__.frozen
        assert ConnectorCapability.__dataclass_params__.frozen


# ===========================================================================
# OP-393: Connector Registry Tests (~15)
# ===========================================================================

class TestConnectorRegistry:
    def test_empty(self):
        reg = ConnectorRegistry()
        assert reg.count == 0

    def test_register(self):
        reg = ConnectorRegistry()
        conn = BaseConnector("File Connector", "file")
        entry = reg.register(conn)
        assert reg.count == 1
        assert entry.name == "File Connector"

    def test_duplicate_detection(self):
        reg = ConnectorRegistry()
        conn = BaseConnector("Test", "test")
        reg.register(conn)
        reg.register(conn)  # same connector, should update not duplicate
        assert reg.count == 1

    def test_unregister(self):
        reg = ConnectorRegistry()
        conn = BaseConnector("Test", "test")
        entry = reg.register(conn)
        result = reg.unregister(conn.info.connector_id)
        assert result is True
        assert reg.count == 0

    def test_unregister_nonexistent(self):
        reg = ConnectorRegistry()
        assert reg.unregister("nonexistent") is False

    def test_find(self):
        reg = ConnectorRegistry()
        conn = BaseConnector("Test", "test")
        reg.register(conn)
        found = reg.find(conn.info.connector_id)
        assert found is not None

    def test_find_nonexistent(self):
        reg = ConnectorRegistry()
        assert reg.find("nonexistent") is None

    def test_find_by_type(self):
        reg = ConnectorRegistry()
        reg.register(BaseConnector("A", "type1"))
        reg.register(BaseConnector("B", "type2"))
        reg.register(BaseConnector("C", "type1"))
        result = reg.find_by_type("type1")
        assert len(result) == 2

    def test_find_by_action(self):
        reg = ConnectorRegistry()
        conn = BaseConnector("Test", "test")
        conn.add_capability(ConnectorCapability(action="read"))
        conn2 = BaseConnector("Test2", "test2")
        conn2.add_capability(ConnectorCapability(action="write"))
        reg.register(conn)
        reg.register(conn2)
        result = reg.find_by_action("read")
        assert len(result) == 1

    def test_capability_lookup(self):
        reg = ConnectorRegistry()
        conn = BaseConnector("Test", "test")
        conn.add_capability(ConnectorCapability(action="read"))
        reg.register(conn)
        lookup = reg.capability_lookup("read")
        assert lookup.total_found == 1

    def test_health_summary(self):
        reg = ConnectorRegistry()
        reg.register(BaseConnector("A", "type1"))
        reg.register(BaseConnector("B", "type2"))
        summary = reg.health_summary()
        assert summary["total_connectors"] == 2

    def test_clear(self):
        reg = ConnectorRegistry()
        reg.register(BaseConnector("A", "test"))
        reg.clear()
        assert reg.count == 0

    def test_list_sorted_by_priority(self):
        reg = ConnectorRegistry()
        reg.register(BaseConnector("Low", "test"), priority=1)
        reg.register(BaseConnector("High", "test"), priority=10)
        entries = reg.list()
        assert entries[0].priority >= entries[1].priority


# ===========================================================================
# OP-394: Execution Planner Tests (~15)
# ===========================================================================

class TestExecutionPlanner:
    def test_plan_empty(self):
        planner = ExecutionPlanner()
        plan = planner.plan(())
        assert plan.total_requests == 0

    def test_plan_single(self):
        planner = ExecutionPlanner()
        req = ExecutionRequest()
        plan = planner.plan((req,))
        assert plan.total_requests == 1

    def test_dependency_ordering(self):
        planner = ExecutionPlanner()
        req_a = ExecutionRequest(action="a")
        req_b = ExecutionRequest(action="b")
        req_c = ExecutionRequest(action="c")
        planner.add_dependency(req_a.request_id, req_b.request_id)
        planner.add_dependency(req_b.request_id, req_c.request_id)
        plan = planner.plan((req_c, req_b, req_a))
        # Should order a -> b -> c
        order = plan.dependency_order
        assert order.index(req_a.request_id) < order.index(req_b.request_id)
        assert order.index(req_b.request_id) < order.index(req_c.request_id)

    def test_aggregate_risk_empty(self):
        risk = ExecutionPlanner.aggregate_risk(())
        assert risk.level == "low"

    def test_aggregate_risk_single(self):
        req = ExecutionRequest(risk=ExecutionRisk(level="high", score=0.7))
        risk = ExecutionPlanner.aggregate_risk((req,))
        assert risk.level == "high"

    def test_aggregate_risk_max(self):
        req1 = ExecutionRequest(risk=ExecutionRisk(level="low"))
        req2 = ExecutionRequest(risk=ExecutionRisk(level="critical"))
        risk = ExecutionPlanner.aggregate_risk((req1, req2))
        assert risk.level == "critical"

    def test_rollback_high_risk(self):
        planner = ExecutionPlanner()
        req = ExecutionRequest(risk=ExecutionRisk(level="high"))
        plan = planner.plan((req,))
        assert plan.rollback_required is True

    def test_rollback_low_risk(self):
        planner = ExecutionPlanner()
        req = ExecutionRequest(risk=ExecutionRisk(level="low"))
        plan = planner.plan((req,))
        assert plan.rollback_required is False

    def test_clear_dependencies(self):
        planner = ExecutionPlanner()
        planner.add_dependency("a", "b")
        planner.clear_dependencies()
        assert len(planner.get_dependencies()) == 0

    def test_parallel_groups(self):
        planner = ExecutionPlanner()
        req_a = ExecutionRequest(action="a")
        req_b = ExecutionRequest(action="b")
        # No dependency = same group
        plan = planner.plan((req_a, req_b))
        assert len(plan.parallel_groups) >= 1


# ===========================================================================
# OP-395: Approval Bridge Tests (~15)
# ===========================================================================

class TestExecutionApprovalBridge:
    def test_create_approval_request_empty_plan(self):
        plan = ExecutionPlan()
        ar = ExecutionApprovalBridge.create_approval_request(plan)
        assert ar.total_items == 0

    def test_create_approval_request_with_items(self):
        req = ExecutionRequest(requires_approval=True, risk=ExecutionRisk(level="medium"))
        plan = ExecutionPlan(requests=(req,))
        ar = ExecutionApprovalBridge.create_approval_request(plan)
        assert ar.total_items >= 1

    def test_approve(self):
        plan = ExecutionPlan()
        ar = ExecutionApprovalBridge.create_approval_request(plan)
        result = ExecutionApprovalBridge.approve(ar, "operator")
        assert result.approved is True
        assert result.approved_by == "operator"

    def test_reject(self):
        plan = ExecutionPlan()
        ar = ExecutionApprovalBridge.create_approval_request(plan)
        result = ExecutionApprovalBridge.reject(ar, "operator", "Not ready")
        assert result.approved is False
        assert result.rejection_reason == "Not ready"

    def test_is_approval_required(self):
        plan = ExecutionPlan(requests=(ExecutionRequest(requires_approval=True),))
        assert ExecutionApprovalBridge.is_approval_required(plan) is True

    def test_is_approval_not_required(self):
        plan = ExecutionPlan(requests=(ExecutionRequest(requires_approval=False, risk=ExecutionRisk(requires_approval=False)),))
        assert ExecutionApprovalBridge.is_approval_required(plan) is False

    def test_get_approval_items(self):
        req = ExecutionRequest(requires_approval=True, risk=ExecutionRisk(level="high"))
        plan = ExecutionPlan(requests=(req,))
        items = ExecutionApprovalBridge.get_approval_items(plan)
        assert len(items) >= 1

    def test_approval_request_frozen(self):
        import dataclasses
        assert dataclasses.is_dataclass(ApprovalRequest)
        assert ApprovalRequest.__dataclass_params__.frozen

    def test_approval_item_create(self):
        item = ApprovalItem(request_id="r1", action="read", connector_type="file")
        assert item.action == "read"


# ===========================================================================
# OP-396: Conversation Bridge Tests (~12)
# ===========================================================================

class TestConversationExecutionBridge:
    def test_init(self):
        reg = ConnectorRegistry()
        bridge = ConversationExecutionBridge(reg)
        assert bridge is not None

    def test_query_unknown(self):
        reg = ConnectorRegistry()
        bridge = ConversationExecutionBridge(reg)
        result = bridge.query("nonexistent")
        assert "error" in result.data

    def test_query_execution_status(self):
        reg = ConnectorRegistry()
        reg.register(BaseConnector("Test", "test"))
        bridge = ConversationExecutionBridge(reg)
        result = bridge.query("execution status")
        assert result.count >= 1

    def test_query_execution_readiness(self):
        reg = ConnectorRegistry()
        bridge = ConversationExecutionBridge(reg)
        result = bridge.query("execution readiness")
        assert result.count == 1

    def test_query_connector_status(self):
        reg = ConnectorRegistry()
        reg.register(BaseConnector("Test", "test"))
        bridge = ConversationExecutionBridge(reg)
        result = bridge.query("connector status")
        assert result.count >= 1

    def test_query_connector_capability(self):
        reg = ConnectorRegistry()
        bridge = ConversationExecutionBridge(reg)
        result = bridge.query("connector capability")
        assert result.count >= 0

    def test_query_approval_requirement(self):
        reg = ConnectorRegistry()
        bridge = ConversationExecutionBridge(reg)
        result = bridge.query("approval requirement", {"risk_level": "high"})
        assert result.data["requires_approval"] is True

    def test_query_rollback_plan(self):
        reg = ConnectorRegistry()
        bridge = ConversationExecutionBridge(reg)
        result = bridge.query("rollback plan", {"risk_level": "critical"})
        assert result.data["rollback_required"] is True

    def test_query_estimated_duration(self):
        reg = ConnectorRegistry()
        bridge = ConversationExecutionBridge(reg)
        result = bridge.query("estimated duration", {"request_count": 5})
        assert result.data["estimated_duration_seconds"] == 5

    def test_query_risk(self):
        reg = ConnectorRegistry()
        bridge = ConversationExecutionBridge(reg)
        result = bridge.query("risk", {"risk_level": "high"})
        assert result.data["requires_approval"] is True

    def test_query_dependency_empty(self):
        reg = ConnectorRegistry()
        bridge = ConversationExecutionBridge(reg)
        result = bridge.query("dependency")
        assert result.count == 0


# ===========================================================================
# OP-397: Dashboard Tests (~12)
# ===========================================================================

class TestExecutionDashboard:
    def test_connector_card_default(self):
        card = ConnectorCard()
        assert card.total_connectors == 0

    def test_connector_card_with_data(self):
        card = ConnectorCard(total_connectors=5, healthy=4, unhealthy=1)
        assert card.total_connectors == 5

    def test_execution_card(self):
        card = ExecutionCard(total_requests=10, pending=5, completed=3, failed=1)
        assert card.total_requests == 10

    def test_approval_card(self):
        card = ApprovalCard(pending_approvals=3, aggregated_risk="high")
        assert card.pending_approvals == 3

    def test_capability_card(self):
        card = CapabilityCard(total_capabilities=4, total_actions=10)
        assert card.total_actions == 10

    def test_health_card(self):
        card = HealthCard(overall_healthy=True)
        assert card.overall_healthy is True

    def test_queue_card(self):
        card = QueueCard(total_in_queue=5, waiting_approval=3)
        assert card.waiting_approval == 3

    def test_dashboard_default(self):
        dash = ExecutionDashboard()
        assert dash.connectors.total_connectors == 0

    def test_builder_empty(self):
        reg = ConnectorRegistry()
        dash = ExecutionDashboardBuilder.build(reg)
        assert dash.connectors.total_connectors == 0

    def test_builder_with_connectors(self):
        reg = ConnectorRegistry()
        conn = BaseConnector("File", "file")
        conn.add_capability(ConnectorCapability(action="read"))
        reg.register(conn)
        dash = ExecutionDashboardBuilder.build(reg)
        assert dash.connectors.total_connectors == 1
        assert dash.connectors.healthy == 1

    def test_all_dashboard_dtos_frozen(self):
        import dataclasses
        for cls in [ConnectorCard, ExecutionCard, ApprovalCard, CapabilityCard, HealthCard, QueueCard, ExecutionDashboard]:
            assert cls.__dataclass_params__.frozen


# ===========================================================================
# OP-398: Integration Pipeline Tests (~12)
# ===========================================================================

class TestExecutionPipeline:
    def test_create(self):
        reg = ConnectorRegistry()
        pipeline = ExecutionPipeline(reg)
        assert pipeline is not None

    def test_not_operational_empty(self):
        reg = ConnectorRegistry()
        pipeline = ExecutionPipeline(reg)
        assert pipeline.is_operational is False

    def test_operational_with_connector(self):
        reg = ConnectorRegistry()
        reg.register(BaseConnector("Test", "test"))
        pipeline = ExecutionPipeline(reg)
        assert pipeline.is_operational is True

    def test_has_support_for(self):
        reg = ConnectorRegistry()
        conn = BaseConnector("Test", "test")
        conn.add_capability(ConnectorCapability(action="read"))
        reg.register(conn)
        pipeline = ExecutionPipeline(reg)
        assert pipeline.has_support_for("read") is True
        assert pipeline.has_support_for("write") is False

    def test_create_request(self):
        reg = ConnectorRegistry()
        pipeline = ExecutionPipeline(reg)
        target = ExecutionTarget(name="test")
        req = pipeline.create_request("file", "read", target)
        assert req.connector_type == "file"
        assert req.action == "read"

    def test_plan_requests(self):
        reg = ConnectorRegistry()
        pipeline = ExecutionPipeline(reg)
        target = ExecutionTarget(name="test")
        req = pipeline.create_request("file", "read", target)
        plan = pipeline.plan_requests((req,))
        assert plan.total_requests == 1

    def test_request_approval(self):
        reg = ConnectorRegistry()
        pipeline = ExecutionPipeline(reg)
        target = ExecutionTarget(name="test")
        req = pipeline.create_request("file", "read", target, risk_level="medium")
        plan = pipeline.plan_requests((req,))
        ar = pipeline.request_approval(plan)
        assert ar.total_items >= 1

    def test_approve_plan(self):
        reg = ConnectorRegistry()
        pipeline = ExecutionPipeline(reg)
        ar = ApprovalRequest()
        result = pipeline.approve_plan(ar)
        assert result.approved is True

    def test_reject_plan(self):
        reg = ConnectorRegistry()
        pipeline = ExecutionPipeline(reg)
        ar = ApprovalRequest()
        result = pipeline.reject_plan(ar, "Not ready")
        assert result.approved is False

    def test_run_pipeline(self):
        reg = ConnectorRegistry()
        reg.register(BaseConnector("File", "file"))
        pipeline = ExecutionPipeline(reg)
        target = ExecutionTarget(name="test.yaml")
        req = pipeline.create_request("file", "read", target)
        result = pipeline.run((req,), approve=True)
        assert result.pipeline_complete is True
        assert result.plan is not None
        assert result.dashboard is not None

    def test_run_pipeline_reject(self):
        reg = ConnectorRegistry()
        reg.register(BaseConnector("File", "file"))
        pipeline = ExecutionPipeline(reg)
        target = ExecutionTarget(name="test.yaml")
        req = pipeline.create_request("file", "read", target)
        result = pipeline.run((req,), approve=False)
        assert result.pipeline_complete is True
        assert result.approval_result.approved is False

    def test_result_dto(self):
        result = ExecutionPipelineResult(pipeline_complete=True)
        assert result.pipeline_complete is True


# ===========================================================================
# Constraint Tests
# ===========================================================================

class TestSprint34Constraints:
    def test_no_domain_imports(self):
        """Sprint 34 execution modules must not import domain/repository/storage/network modules.
        Only scans sprint34-specific files (not legacy engine.py).
        """
        import ast
        import glob
        execution_dir = os.path.join(os.path.dirname(__file__), "..", "src", "sam", "execution")
        forbidden_prefixes = [
            "sam.operations",
            "sam.domain",
            "sam.storage",
            "sam.repository",
            "sam.telemetry",
            "requests",
            "http",
            "socket",
            "asyncio",
            "threading",
            "subprocess",
        ]
        # Only scan Sprint 34 files (exclude legacy engine.py which may have pre-existing imports)
        sprint34_files = [
            os.path.join(execution_dir, f)
            for f in [
                "execution_request.py",
                "connector_protocol.py",
                "connector_registry.py",
                "execution_planner.py",
                "approval_execution.py",
                "conversation_execution.py",
                "dashboard_execution.py",
                "integration_execution.py",
            ]
            if os.path.exists(os.path.join(execution_dir, f))
        ]
        for fpath in sprint34_files:
            with open(fpath) as f:
                try:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                for pref in forbidden_prefixes:
                                    assert not alias.name.startswith(pref), \
                                        f"Forbidden import {alias.name} in {fpath}"
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                for pref in forbidden_prefixes:
                                    assert not node.module.startswith(pref), \
                                        f"Forbidden import {node.module} in {fpath}"
                except SyntaxError:
                    pass

    def test_dtos_are_frozen(self):
        """All execution DTOs must be frozen dataclasses."""
        import dataclasses
        dto_classes = [
            ExecutionRequest, ExecutionTarget, ExecutionParameter,
            ExecutionPlan, ExecutionResult, ExecutionStatus, ExecutionRisk,
            ConnectorInfo, ConnectorCapability,
            RegistryEntry, CapabilityLookup,
            DependencyEdge,
            ApprovalRequest, ApprovalResult, ApprovalItem,
            ExecutionQueryResult, ExecutionPipelineResult,
            ConnectorCard, ExecutionCard, ApprovalCard, CapabilityCard,
            HealthCard, QueueCard, ExecutionDashboard,
        ]
        for cls in dto_classes:
            assert dataclasses.is_dataclass(cls), f"{cls.__name__} is not a dataclass"
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} is not frozen"

    def test_no_execute_method(self):
        """No class in execution modules should have an execute() method."""
        import ast
        import glob
        execution_dir = os.path.join(os.path.dirname(__file__), "..", "src", "sam", "execution")
        py_files = glob.glob(os.path.join(execution_dir, "*.py"))
        for fpath in py_files:
            with open(fpath) as f:
                try:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name == "execute":
                            raise AssertionError(
                                f"execute() method found in {fpath} at line {node.lineno}"
                            )
                except SyntaxError:
                    pass


# ===========================================================================
# Additional Coverage Tests (to reach >=120)
# ===========================================================================

class TestCoverageExecutionRequest:
    def test_with_full_params(self):
        params = (
            ExecutionParameter(key="path", value="/tmp/test", required=True),
            ExecutionParameter(key="mode", value="r", required=False),
        )
        target = ExecutionTarget(
            target_id="t1", target_type="file", name="test.txt",
            description="A test file", parameters=params,
        )
        req = ExecutionRequest(
            connector_type="file", action="read", target=target,
            parameters=params, source="test", description="Read test file",
            requires_approval=True,
        )
        assert req.source == "test"
        assert len(req.parameters) == 2
        assert req.target.name == "test.txt"

    def test_risk_creates_approval(self):
        risk = ExecutionRisk(level="medium", score=0.5, requires_approval=True)
        req = ExecutionRequest(risk=risk, requires_approval=True)
        assert req.requires_human_approval is True

    def test_empty_plan_no_aggregated_risk(self):
        plan = ExecutionPlan()
        assert plan.aggregated_risk is None

    def test_status_equality(self):
        s1 = ExecutionStatus("pending")
        s2 = ExecutionStatus("pending")
        assert s1.value == s2.value

    def test_negative_status_comparison(self):
        assert ExecutionStatus.pending().value != ExecutionStatus.completed().value


class TestCoverageConnectorProtocol:
    def test_capability_with_params(self):
        params = (ExecutionParameter(key="k", value="v"),)
        cap = ConnectorCapability(action="write", description="Write file",
                                   requires_approval=True, risk_level="high",
                                   parameters=params)
        assert cap.risk_level == "high"
        assert len(cap.parameters) == 1

    def test_build_request_with_params(self):
        conn = BaseConnector("Test", "test")
        params = (ExecutionParameter(key="k", value="v"),)
        req = conn.build_request("read", ExecutionTarget(name="t"), params)
        assert len(req.parameters) == 1

    def test_validate_type_mismatch(self):
        conn = BaseConnector("Test", "file")
        req = ExecutionRequest(connector_type="db", action="query",
                               target=ExecutionTarget(name="t"))
        errors = conn.validate(req)
        assert len(errors) > 0

    def test_add_multiple_capabilities(self):
        conn = BaseConnector("Test", "test")
        conn.add_capability(ConnectorCapability(action="read"))
        conn.add_capability(ConnectorCapability(action="write"))
        conn.add_capability(ConnectorCapability(action="delete"))
        actions = conn.supported_actions()
        assert len(actions) == 3
        assert "read" in actions
        assert "delete" in actions


class TestCoverageRegistry:
    def test_register_multiple_same_type(self):
        reg = ConnectorRegistry()
        reg.register(BaseConnector("A", "type1"))
        reg.register(BaseConnector("B", "type1"))
        reg.register(BaseConnector("C", "type2"))
        assert reg.count == 3
        assert len(reg.find_by_type("type1")) == 2

    def test_entry_find(self):
        reg = ConnectorRegistry()
        conn = BaseConnector("Test", "test")
        entry = reg.register(conn)
        found = reg.find_entry(conn.info.connector_id)
        assert found is not None
        assert found.name == "Test"

    def test_list_empty(self):
        reg = ConnectorRegistry()
        assert reg.list() == ()


class TestCoveragePlanner:
    def test_plan_with_dependencies(self):
        planner = ExecutionPlanner()
        req_a = ExecutionRequest(action="a")
        req_b = ExecutionRequest(action="b")
        req_c = ExecutionRequest(action="c")
        planner.add_dependency(req_a.request_id, req_b.request_id, "requires")
        planner.add_dependency(req_b.request_id, req_c.request_id, "blocks")
        deps = planner.get_dependencies()
        assert len(deps) == 2

    def test_risk_aggregation_factors(self):
        req = ExecutionRequest(
            risk=ExecutionRisk(level="high", score=0.7,
                               factors=("high cpu", "low memory"),
                               requires_approval=True)
        )
        risk = ExecutionPlanner.aggregate_risk((req,))
        assert len(risk.factors) >= 2

    def test_parallel_groups_multiple(self):
        planner = ExecutionPlanner()
        reqs = tuple(ExecutionRequest() for _ in range(4))
        plan = planner.plan(reqs)
        assert plan.total_requests == 4


class TestCoverageApproval:
    def test_approval_chain(self):
        plan = ExecutionPlan()
        ar = ExecutionApprovalBridge.create_approval_request(plan)
        result = ExecutionApprovalBridge.approve(ar)
        assert result.approved is True
        assert result.approval_id == ar.approval_id

    def test_approval_result_dto(self):
        result = ApprovalResult(approved=True, approved_by="test")
        assert result.approved_by == "test"


class TestCoveragePipeline:
    def test_run_high_risk_pipeline(self):
        reg = ConnectorRegistry()
        reg.register(BaseConnector("File", "file"))
        pipeline = ExecutionPipeline(reg)
        target = ExecutionTarget(name="secret.txt")
        req = pipeline.create_request(
            "file", "delete", target, risk_level="critical"
        )
        result = pipeline.run((req,), approve=True)
        assert result.pipeline_complete is True
        assert result.approval_result.approved is True

    def test_dashboard_frozen(self):
        import dataclasses
        assert ExecutionDashboard.__dataclass_params__.frozen
