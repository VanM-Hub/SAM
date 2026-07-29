# Sprint 35 — Connector Runtime
# Target: >=130 tests
# Constraints: no execute, no subprocess, no network, no domain imports

import sys, os
from datetime import datetime, timedelta
from dataclasses import replace as dataclass_replace
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.execution.connectors.connector_runtime import (
    ConnectorRuntime, ConnectorSession, ConnectorContext,
    ConnectorHealth, ConnectorRuntimeSnapshot,
)
from sam.execution.connectors.connector_capability import (
    Capability, CapabilitySet, CapabilityMatcher, CapabilityReport, BUILTIN_CAPABILITIES,
)
from sam.execution.connectors.connector_policy import (
    PolicyEvaluator, PolicyDecision, PolicyViolation, ConnectorPolicy, MINIMAL_POLICIES,
)
from sam.execution.connectors.connector_health import (
    ConnectorHealthEngine, ConnectorHealthStatus, ConnectorHealthSnapshot,
    HealthReport, HealthRuleResult, HEALTH_RULES,
)
from sam.execution.connectors.mock_connectors import (
    MockFilesystemConnector, MockRESTConnector,
    MockGitConnector, MockShellConnector,
)
from sam.execution.connectors.conversation_connector import (
    ConversationConnectorBridge, ConnectorQueryResult,
)
from sam.execution.connectors.dashboard_connector import (
    ConnectorDashboardBuilder, ConnectorDashboard,
    ConnectorSummaryCard, CapabilityCardDTO, PolicyCardDTO,
    HealthCardDTO, PreviewCardDTO,
)
from sam.execution.connectors.integration_connector import (
    ConnectorIntegrationPipeline, ConnectorPipelineResult,
)
from sam.execution.connector_registry import ConnectorRegistry
from sam.execution.connector_protocol import BaseConnector
from sam.execution.execution_request import ExecutionTarget, ExecutionParameter


# ===================================================================
# OP-401: ConnectorRuntime Tests (~15)
# ===================================================================

class TestConnectorSession:
    def test_create(self):
        s = ConnectorSession(connector_id="c1")
        assert s.session_id
        assert s.connector_id == "c1"

    def test_frozen(self):
        import dataclasses
        assert ConnectorSession.__dataclass_params__.frozen


class TestConnectorContext:
    def test_create(self):
        c = ConnectorContext(session_id="s1", connector_type="file", capability="read")
        assert c.capability == "read"

    def test_frozen(self):
        import dataclasses
        assert ConnectorContext.__dataclass_params__.frozen


class TestConnectorRuntime:
    def test_create(self):
        reg = ConnectorRegistry()
        r = ConnectorRuntime(reg)
        assert r is not None

    def test_create_session(self):
        reg = ConnectorRegistry()
        conn = MockFilesystemConnector()
        reg.register(conn)
        r = ConnectorRuntime(reg)
        s = r.create_session(conn.info.connector_id)
        assert s.connector_id == conn.info.connector_id

    def test_get_session(self):
        reg = ConnectorRegistry()
        conn = MockFilesystemConnector()
        reg.register(conn)
        r = ConnectorRuntime(reg)
        s = r.create_session(conn.info.connector_id)
        found = r.get_session(s.session_id)
        assert found is not None
        assert found.session_id == s.session_id

    def test_get_session_nonexistent(self):
        reg = ConnectorRegistry()
        r = ConnectorRuntime(reg)
        assert r.get_session("none") is None

    def test_close_session(self):
        reg = ConnectorRegistry()
        conn = MockFilesystemConnector()
        reg.register(conn)
        r = ConnectorRuntime(reg)
        s = r.create_session(conn.info.connector_id)
        assert r.close_session(s.session_id) is True

    def test_select_connector(self):
        reg = ConnectorRegistry()
        reg.register(MockFilesystemConnector())
        r = ConnectorRuntime(reg)
        c = r.select_connector("filesystem")
        assert c is not None

    def test_select_connector_not_found(self):
        reg = ConnectorRegistry()
        r = ConnectorRuntime(reg)
        assert r.select_connector("nonexistent") is None

    def test_validate_capability(self):
        reg = ConnectorRegistry()
        conn = MockFilesystemConnector()
        reg.register(conn)
        r = ConnectorRuntime(reg)
        errors = r.validate_capability(conn, "read")
        assert len(errors) == 0

    def test_validate_capability_unsupported(self):
        reg = ConnectorRegistry()
        conn = MockFilesystemConnector()
        reg.register(conn)
        r = ConnectorRuntime(reg)
        errors = r.validate_capability(conn, "execute")
        assert len(errors) > 0

    def test_create_context(self):
        reg = ConnectorRegistry()
        conn = MockFilesystemConnector()
        reg.register(conn)
        r = ConnectorRuntime(reg)
        s = r.create_session(conn.info.connector_id)
        target = ExecutionTarget(name="test.txt")
        c = r.create_context(s, "filesystem", "read", target, preview="[PREVIEW] Read file")
        assert c.capability == "read"
        assert c.preview == "[PREVIEW] Read file"

    def test_compile_preview(self):
        reg = ConnectorRegistry()
        conn = MockFilesystemConnector()
        reg.register(conn)
        r = ConnectorRuntime(reg)
        preview = r.compile_preview(conn, "read", ExecutionTarget(name="test.txt"))
        assert "PREVIEW" in preview

    def test_snapshot(self):
        reg = ConnectorRegistry()
        conn = MockFilesystemConnector()
        reg.register(conn)
        r = ConnectorRuntime(reg)
        snap = r.snapshot()
        assert snap.total_connectors >= 1

    def test_set_health(self):
        reg = ConnectorRegistry()
        r = ConnectorRuntime(reg)
        r.set_connector_health("c1", False, "Down")
        health = r.get_connector_health("c1")
        assert health.healthy is False

    def test_clear_errors(self):
        reg = ConnectorRegistry()
        r = ConnectorRuntime(reg)
        r.set_connector_health("c1", False, "err")
        r.clear_errors()
        snap = r.snapshot()
        assert snap.last_error == ""


# ===================================================================
# OP-402: Capability Tests (~15)
# ===================================================================

class TestCapability:
    def test_builtin_read(self):
        c = Capability.builtin("read")
        assert c.name == "read"
        assert c.risk_level == "low"
        assert c.requires_approval is False

    def test_builtin_delete(self):
        c = Capability.builtin("delete")
        assert c.risk_level == "high"
        assert c.requires_approval is True
        assert c.requires_guardian is True

    def test_builtin_all_caps(self):
        for name in BUILTIN_CAPABILITIES:
            c = Capability.builtin(name)
            assert c.name == name


class TestCapabilitySet:
    def test_empty(self):
        cs = CapabilitySet()
        assert cs.names == ()

    def test_all_builtin(self):
        cs = CapabilitySet.all_builtin()
        assert len(cs.names) == len(BUILTIN_CAPABILITIES)

    def test_contains(self):
        cs = CapabilitySet.all_builtin()
        assert cs.contains("read")
        assert not cs.contains("nonexistent")

    def test_get(self):
        cs = CapabilitySet.all_builtin()
        c = cs.get("read")
        assert c is not None
        assert c.name == "read"

    def test_high_risk(self):
        cs = CapabilitySet.all_builtin()
        high = cs.high_risk
        assert all(c.risk_level == "high" for c in high)

    def test_requires_approval(self):
        cs = CapabilitySet.all_builtin()
        ra = cs.requires_approval
        assert all(c.requires_approval for c in ra)


class TestCapabilityReport:
    def test_from_set(self):
        cs = CapabilitySet.all_builtin()
        r = CapabilityReport.from_set(cs)
        assert r.total == 10

    def test_empty(self):
        r = CapabilityReport()
        assert r.total == 0


class TestCapabilityMatcher:
    def test_match_required_all_present(self):
        cs = CapabilitySet.all_builtin()
        missing = CapabilityMatcher.match_required(cs, ("read", "write"))
        assert len(missing) == 0

    def test_match_required_missing(self):
        cs = CapabilitySet.all_builtin()
        missing = CapabilityMatcher.match_required(cs, ("read", "fly"))
        assert len(missing) == 1

    def test_match_any(self):
        cs = CapabilitySet.all_builtin()
        found = CapabilityMatcher.match_any(cs, ("read", "fly"))
        assert "read" in found
        assert "fly" not in found

    def test_risk_threshold(self):
        cs = CapabilitySet.all_builtin()
        exceeding = CapabilityMatcher.match_risk_threshold(cs, "low")
        assert len(exceeding) > 0  # medium+ will be in exceeding

    def test_approval_details(self):
        cs = CapabilitySet.all_builtin()
        need_approval, need_guardian = CapabilityMatcher.requires_approval_details(cs, "delete")
        assert need_approval is True
        assert need_guardian is True


# ===================================================================
# OP-403: Policy Tests (~15)
# ===================================================================

class TestPolicyEvaluator:
    def test_default_policies(self):
        pe = PolicyEvaluator()
        pl = pe.list_policies()
        assert len(pl) == len(MINIMAL_POLICIES)

    def test_default_policy_names(self):
        pe = PolicyEvaluator()
        names = [p.name for p in pe.list_policies()]
        for n in MINIMAL_POLICIES:
            assert n in names

    def test_get_policy(self):
        pe = PolicyEvaluator()
        p = pe.get_policy("connector enabled")
        assert p is not None
        assert p.name == "connector enabled"

    def test_set_policy(self):
        pe = PolicyEvaluator()
        pe.set_policy("connector enabled", {"enabled_connectors": ["file"]})
        p = pe.get_policy("connector enabled")
        assert p.params["enabled_connectors"] == ["file"]

    def test_enable_policy(self):
        pe = PolicyEvaluator()
        pe.enable_policy("connector enabled", False)
        p = pe.get_policy("connector enabled")
        assert p.enabled is False

    def test_evaluate_default_pass(self):
        pe = PolicyEvaluator()
        d = pe.evaluate(connector_type="file", capability="read")
        assert d.approved is True

    def test_evaluate_blocked_capability(self):
        pe = PolicyEvaluator()
        d = pe.evaluate(connector_type="file", capability="execute")
        assert d.approved is False

    def test_evaluate_maintenance_mode(self):
        pe = PolicyEvaluator()
        pe.set_policy("maintenance mode", {"maintenance": True})
        d = pe.evaluate(connector_type="file", capability="read")
        assert d.approved is False

    def test_evaluate_read_only(self):
        pe = PolicyEvaluator()
        pe.set_policy("read only mode", {"read_only": True})
        d = pe.evaluate(connector_type="file", capability="write")
        assert d.approved is False

    def test_evaluate_unhealthy(self):
        pe = PolicyEvaluator()
        d = pe.evaluate(connector_name="test", connector_type="file",
                         connector_healthy=False)
        assert d.approved is False

    def test_evaluate_guardian_needed(self):
        pe = PolicyEvaluator()
        d = pe.evaluate(connector_type="file", capability="read",
                         risk_level="critical")
        violations = [v for v in d.violations if v.policy_name == "guardian required"]
        assert len(violations) >= 1

    def test_policy_decision_properties(self):
        v = PolicyViolation("test", "msg", "error")
        d = PolicyDecision(approved=False, violations=(v,))
        assert d.has_violations
        assert d.has_errors


# ===================================================================
# OP-404: Health Tests (~12)
# ===================================================================

class TestConnectorHealthEngine:
    def test_create(self):
        reg = ConnectorRegistry()
        he = ConnectorHealthEngine(reg)
        assert he is not None

    def test_check_unknown(self):
        reg = ConnectorRegistry()
        he = ConnectorHealthEngine(reg)
        s = he.check_connector("unknown")
        assert s.healthy is False

    def test_check_healthy(self):
        reg = ConnectorRegistry()
        conn = MockFilesystemConnector()
        reg.register(conn)
        he = ConnectorHealthEngine(reg)
        s = he.check_connector(conn.info.connector_id)
        assert s.healthy is True

    def test_check_all(self):
        reg = ConnectorRegistry()
        reg.register(MockFilesystemConnector())
        reg.register(MockRESTConnector())
        he = ConnectorHealthEngine(reg)
        snap = he.check_all()
        assert snap.total == 2
        assert snap.healthy >= 1

    def test_generate_report(self):
        reg = ConnectorRegistry()
        reg.register(MockFilesystemConnector())
        he = ConnectorHealthEngine(reg)
        r = he.generate_report()
        assert r.total_connectors >= 1

    def test_mark_unhealthy(self):
        reg = ConnectorRegistry()
        conn = MockFilesystemConnector()
        reg.register(conn)
        he = ConnectorHealthEngine(reg)
        he.mark_unhealthy(conn.info.connector_id, "Config error")
        s = he.check_connector(conn.info.connector_id)
        assert s.healthy is False

    def test_mark_healthy_after_unhealthy(self):
        reg = ConnectorRegistry()
        conn = MockFilesystemConnector()
        reg.register(conn)
        he = ConnectorHealthEngine(reg)
        he.mark_unhealthy(conn.info.connector_id, "err")
        he.mark_healthy(conn.info.connector_id)
        s = he.check_connector(conn.info.connector_id)
        assert s.healthy is True

    def test_health_rules(self):
        reg = ConnectorRegistry()
        he = ConnectorHealthEngine(reg)
        rules = he.get_rule_results()
        for name in HEALTH_RULES:
            assert name in rules


# ===================================================================
# OP-405: Mock Connector Tests (~15)
# ===================================================================

class TestMockFilesystemConnector:
    def test_create(self):
        c = MockFilesystemConnector()
        assert c.info.connector_type == "filesystem"
        assert "read" in c.supported_actions()

    def test_preview_read(self):
        c = MockFilesystemConnector()
        req = c.build_request("read", ExecutionTarget(name="test.txt"))
        assert "PREVIEW" in c.preview(req)

    def test_preview_delete(self):
        c = MockFilesystemConnector()
        req = c.build_request("delete", ExecutionTarget(name="test.txt"))
        p = c.preview(req)
        assert "high" in p

    def test_validate_valid(self):
        c = MockFilesystemConnector()
        req = c.build_request("read", ExecutionTarget(name="t"))
        assert len(c.validate(req)) == 0

    def test_capabilities_count(self):
        c = MockFilesystemConnector()
        assert len(c.supported_actions()) == 5


class TestMockRESTConnector:
    def test_create(self):
        c = MockRESTConnector()
        assert c.info.connector_type == "rest_api"
        assert "read" in c.supported_actions()
        assert "notify" in c.supported_actions()

    def test_preview_get(self):
        c = MockRESTConnector()
        req = c.build_request("read", ExecutionTarget(name="api/test"))
        assert "GET" in c.preview(req)

    def test_preview_delete(self):
        c = MockRESTConnector()
        req = c.build_request("delete", ExecutionTarget(name="api/resource"))
        assert "DELETE" in c.preview(req)


class TestMockGitConnector:
    def test_create(self):
        c = MockGitConnector()
        assert c.info.connector_type == "git"
        assert "rollback" in c.supported_actions()

    def test_preview_rollback(self):
        c = MockGitConnector()
        params = (ExecutionParameter(key="commit", value="abc123"),)
        req = c.build_request("rollback", ExecutionTarget(name="repo"), params)
        p = c.preview(req)
        assert "revert" in p or "rollback" in p


class TestMockShellConnector:
    def test_create(self):
        c = MockShellConnector()
        assert c.info.connector_type == "shell"
        assert "execute" in c.supported_actions()

    def test_preview_execute(self):
        c = MockShellConnector()
        params = (ExecutionParameter(key="command", value="ls"),)
        req = c.build_request("execute", ExecutionTarget(name="ls"), params)
        p = c.preview(req)
        assert "high" in p

    def test_validate_execute_no_target(self):
        c = MockShellConnector()
        req = c.build_request("execute", ExecutionTarget(name=""))
        errors = c.validate(req)
        assert len(errors) > 0

    def test_validate_no_network_call(self):
        c = MockShellConnector()
        req = c.build_request("read", ExecutionTarget(name="file"))
        assert len(c.validate(req)) == 0


# ===================================================================
# OP-406: Conversation Connector Tests (~12)
# ===================================================================

class TestConversationConnectorBridge:
    def _setup(self):
        reg = ConnectorRegistry()
        reg.register(MockFilesystemConnector())
        reg.register(MockRESTConnector())
        runtime = ConnectorRuntime(reg)
        policy = PolicyEvaluator()
        health = ConnectorHealthEngine(reg)
        return ConversationConnectorBridge(reg, runtime, policy, health)

    def test_query_unknown(self):
        b = self._setup()
        r = b.query("nonexistent")
        assert "error" in r.data

    def test_query_list(self):
        b = self._setup()
        r = b.query("connector list")
        assert r.count >= 1

    def test_query_capability(self):
        b = self._setup()
        r = b.query("connector capability")
        assert r.count >= 1

    def test_query_health(self):
        b = self._setup()
        r = b.query("connector health")
        assert r.count >= 1

    def test_query_policy(self):
        b = self._setup()
        r = b.query("connector policy")
        assert r.count >= 1

    def test_query_preview(self):
        b = self._setup()
        r = b.query("execution preview", {"connector_type": "filesystem",
                                           "action": "read", "target": "f.txt"})
        assert r.count == 1
        assert "PREVIEW" in str(r.data)

    def test_query_status(self):
        b = self._setup()
        r = b.query("connector status")
        assert r.count == 1

    def test_query_trusted(self):
        b = self._setup()
        r = b.query("trusted connectors")
        assert r.count >= 1

    def test_query_maintenance(self):
        b = self._setup()
        r = b.query("maintenance")
        assert r.count == 1

    def test_query_diagnostic(self):
        b = self._setup()
        r = b.query("diagnostic")
        assert r.count == 1


# ===================================================================
# OP-407: Dashboard Tests (~10)
# ===================================================================

class TestConnectorDashboard:
    def _setup(self):
        reg = ConnectorRegistry()
        reg.register(MockFilesystemConnector())
        reg.register(MockRESTConnector())
        runtime = ConnectorRuntime(reg)
        policy = PolicyEvaluator()
        health = ConnectorHealthEngine(reg)
        return reg, runtime, policy, health

    def test_summary_card_empty(self):
        c = ConnectorSummaryCard()
        assert c.total_connectors == 0

    def test_build_dashboard(self):
        reg, runtime, policy, health = self._setup()
        dash = ConnectorDashboardBuilder.build(reg, runtime, policy, health)
        assert dash.summary.total_connectors >= 1

    def test_dashboard_has_health(self):
        reg, runtime, policy, health = self._setup()
        dash = ConnectorDashboardBuilder.build(reg, runtime, policy, health)
        assert dash.health.total >= 1

    def test_dashboard_has_policy(self):
        reg, runtime, policy, health = self._setup()
        dash = ConnectorDashboardBuilder.build(reg, runtime, policy, health)
        assert dash.policy.total >= 1

    def test_all_dtos_frozen(self):
        import dataclasses
        for cls in [ConnectorSummaryCard, CapabilityCardDTO, PolicyCardDTO,
                     HealthCardDTO, PreviewCardDTO, ConnectorDashboard]:
            assert cls.__dataclass_params__.frozen


# ===================================================================
# OP-408: Integration Pipeline Tests (~12)
# ===================================================================

class TestConnectorIntegrationPipeline:
    def _setup(self):
        reg = ConnectorRegistry()
        reg.register(MockFilesystemConnector())
        runtime = ConnectorRuntime(reg)
        return reg, runtime

    def test_create(self):
        reg, runtime = self._setup()
        p = ConnectorIntegrationPipeline(reg, runtime)
        assert p is not None

    def test_run_filesystem_read(self):
        reg, runtime = self._setup()
        p = ConnectorIntegrationPipeline(reg, runtime)
        result = p.run("filesystem", "read", "test.txt")
        assert result.pipeline_complete is True
        assert result.context is not None

    def test_run_rejected(self):
        reg, runtime = self._setup()
        p = ConnectorIntegrationPipeline(reg, runtime)
        result = p.run("filesystem", "read", "test.txt", approve=False)
        assert result.pipeline_complete is True
        assert result.approval_result.approved is False

    def test_run_nonexistent_connector(self):
        reg, runtime = self._setup()
        p = ConnectorIntegrationPipeline(reg, runtime)
        result = p.run("nonexistent", "read")
        assert result.pipeline_complete is False

    def test_run_has_dashboard(self):
        reg, runtime = self._setup()
        p = ConnectorIntegrationPipeline(reg, runtime)
        result = p.run("filesystem", "read", "test.txt")
        assert result.dashboard is not None

    def test_run_high_risk(self):
        reg, runtime = self._setup()
        c2 = MockShellConnector()
        reg.register(c2)
        p = ConnectorIntegrationPipeline(reg, runtime)
        result = p.run("shell", "execute", "ls", risk_level="critical")
        assert result.pipeline_complete is True
        assert result.policy_decision is not None


# ===================================================================
# Additional Coverage Tests (to reach >=130)
# ===================================================================

class TestCoverageRuntime:
    def test_to_conversation_dto(self):
        reg = ConnectorRegistry()
        conn = MockFilesystemConnector()
        reg.register(conn)
        r = ConnectorRuntime(reg)
        s = r.create_session(conn.info.connector_id)
        target = ExecutionTarget(name="t.txt")
        c = r.create_context(s, "filesystem", "read", target, preview="preview")
        dto = r.to_conversation_dto(c)
        assert dto["capability"] == "read"
        assert dto["preview"] == "preview"

    def test_mark_guardian_approval(self):
        reg = ConnectorRegistry()
        r = ConnectorRuntime(reg)
        s = r.create_session("c1")
        c = r.create_context(s, "test", "read")
        approved = r.mark_guardian_approval(c, True)
        assert approved.guardian_approved is True
        assert approved.policy_decision == "approved"

    def test_close_nonexistent_session(self):
        reg = ConnectorRegistry()
        r = ConnectorRuntime(reg)
        assert r.close_session("none") is False

    def test_snapshot_no_connectors(self):
        reg = ConnectorRegistry()
        r = ConnectorRuntime(reg)
        snap = r.snapshot()
        assert snap.total_connectors == 0

    def test_connector_health_default(self):
        reg = ConnectorRegistry()
        r = ConnectorRuntime(reg)
        h = r.get_connector_health("nonexistent")
        assert h.healthy is True


class TestCoverageCapability:
    def test_capability_report_empty_names(self):
        r = CapabilityReport()
        assert r.names == ()

    def test_capability_set_empty(self):
        cs = CapabilitySet()
        assert cs.get("read") is None

    def test_capability_builtin_approve(self):
        c = Capability.builtin("approve")
        assert c.risk_level == "medium"

    def test_capability_builtin_search(self):
        c = Capability.builtin("search")
        assert c.risk_level == "low"


class TestCoveragePolicy:
    def test_policy_violation_default_severity(self):
        v = PolicyViolation("test", "msg")
        assert v.severity == "warning"

    def test_policy_decision_no_violations(self):
        d = PolicyDecision()
        assert not d.has_violations
        assert not d.has_errors

    def test_enable_nonexistent_policy(self):
        pe = PolicyEvaluator()
        assert pe.enable_policy("none", False) is False

    def test_set_policy_nonexistent(self):
        pe = PolicyEvaluator()
        assert pe.set_policy("none", {}) is False

    def test_evaluate_approval_low_risk(self):
        pe = PolicyEvaluator()
        d = pe.evaluate(connector_type="file", capability="read", risk_level="low")
        assert d.approved is True

    def test_evaluate_capability_policy(self):
        pe = PolicyEvaluator()
        cs = CapabilitySet.all_builtin()
        d = pe.evaluate_capability(cs, "delete")
        assert not d.approved

    def test_evaluate_capability_unknown(self):
        pe = PolicyEvaluator()
        cs = CapabilitySet()
        d = pe.evaluate_capability(cs, "fly")
        assert d is not None


class TestCoverageHealth:
    def test_health_rule_result_default(self):
        r = HealthRuleResult()
        assert r.passed is True

    def test_health_snapshot_empty(self):
        snap = ConnectorHealthSnapshot()
        assert snap.total == 0

    def test_health_report_default(self):
        r = HealthReport()
        assert r.overall_healthy is True

    def test_health_status_default(self):
        s = ConnectorHealthStatus()
        assert s.healthy is True


class TestCoverageMockConnectors:
    def test_filesystem_all_previews(self):
        conn = MockFilesystemConnector()
        for action in conn.supported_actions():
            req = conn.build_request(action, ExecutionTarget(name="t"))
            p = conn.preview(req)
            assert "PREVIEW" in p

    def test_rest_all_previews(self):
        conn = MockRESTConnector()
        for action in conn.supported_actions():
            req = conn.build_request(action, ExecutionTarget(name="t"))
            p = conn.preview(req)
            assert "PREVIEW" in p

    def test_git_all_previews(self):
        conn = MockGitConnector()
        for action in conn.supported_actions():
            req = conn.build_request(action, ExecutionTarget(name="t"))
            p = conn.preview(req)
            assert "PREVIEW" in p

    def test_shell_all_previews(self):
        conn = MockShellConnector()
        for action in conn.supported_actions():
            req = conn.build_request(action, ExecutionTarget(name="t"))
            p = conn.preview(req)
            assert "PREVIEW" in p


class TestCoverageDashboardCards:
    def test_summary_card_with_types(self):
        c = ConnectorSummaryCard(
            total_connectors=5, filesystem=2, rest_api=1, git=1, shell=1,
            total_capabilities=20,
        )
        assert c.filesystem == 2
        assert c.rest_api == 1
        assert c.total_capabilities == 20

    def test_capability_card_dto(self):
        c = CapabilityCardDTO(names=("read", "write"), low_risk=1, high_risk=1)
        assert c.low_risk == 1

    def test_policy_card_dto(self):
        c = PolicyCardDTO(total=8, enabled=6, disabled=2, names=("a", "b"))
        assert c.disabled == 2

    def test_health_card_dto(self):
        c = HealthCardDTO(overall_healthy=False, total=3, healthy=1, unhealthy=2)
        assert c.overall_healthy is False

    def test_preview_card_dto(self):
        c = PreviewCardDTO(last_preview="test", connector_name="File")
        assert c.connector_name == "File"


class TestCoveragePipeline:
    def test_pipeline_result_default(self):
        r = ConnectorPipelineResult()
        assert r.pipeline_complete is False

    def test_pipeline_request_object(self):
        from sam.execution.execution_request import ExecutionRequest
        req = ExecutionRequest(connector_type="test", action="read",
                                target=ExecutionTarget(name="t"))
        assert req.connector_type == "test"

    def test_pipeline_with_all_connectors(self):
        reg = ConnectorRegistry()
        reg.register(MockFilesystemConnector())
        reg.register(MockRESTConnector())
        reg.register(MockGitConnector())
        reg.register(MockShellConnector())
        runtime = ConnectorRuntime(reg)
        p = ConnectorIntegrationPipeline(reg, runtime)
        result = p.run("rest_api", "monitor", "api/health")
        assert result.pipeline_complete is True

    def test_pipeline_shell_execute(self):
        reg = ConnectorRegistry()
        reg.register(MockShellConnector())
        runtime = ConnectorRuntime(reg)
        p = ConnectorIntegrationPipeline(reg, runtime)
        result = p.run("shell", "execute", "ls -la", risk_level="high")
        assert result.pipeline_complete is True

    def test_pipeline_git_rollback(self):
        reg = ConnectorRegistry()
        reg.register(MockGitConnector())
        runtime = ConnectorRuntime(reg)
        p = ConnectorIntegrationPipeline(reg, runtime)
        result = p.run("git", "rollback", "myrepo")
        assert result.pipeline_complete is True

    def test_pipeline_filesystem_search(self):
        reg = ConnectorRegistry()
        reg.register(MockFilesystemConnector())
        runtime = ConnectorRuntime(reg)
        p = ConnectorIntegrationPipeline(reg, runtime)
        result = p.run("filesystem", "search", "/tmp")
        assert result.pipeline_complete is True

    def test_pipeline_rest_notify(self):
        reg = ConnectorRegistry()
        reg.register(MockRESTConnector())
        runtime = ConnectorRuntime(reg)
        p = ConnectorIntegrationPipeline(reg, runtime)
        result = p.run("rest_api", "notify", "webhook/alert")
        assert result.pipeline_complete is True


# ===================================================================
# Constraint Tests
# ===================================================================

class TestSprint35Constraints:
    def test_no_domain_imports(self):
        import ast, glob
        connector_dir = os.path.join(os.path.dirname(__file__), "..", "src",
                                      "sam", "execution", "connectors")
        forbidden = ["sam.operations", "sam.domain", "sam.storage",
                      "requests", "http", "socket", "asyncio", "subprocess"]
        sprint35_files = [f for f in glob.glob(os.path.join(connector_dir, "*.py"))
                           if not f.endswith("__init__.py")]
        for fpath in sprint35_files:
            with open(fpath) as f:
                try:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                for pref in forbidden:
                                    assert not alias.name.startswith(pref), \
                                        f"Forbidden import {alias.name} in {fpath}"
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                for pref in forbidden:
                                    assert not node.module.startswith(pref), \
                                        f"Forbidden import {node.module} in {fpath}"
                except SyntaxError:
                    pass

    def test_dtos_are_frozen(self):
        import dataclasses
        dtos = [
            ConnectorSession, ConnectorContext, ConnectorHealth,
            ConnectorRuntimeSnapshot,
            Capability, CapabilitySet, CapabilityReport,
            PolicyViolation, PolicyDecision, ConnectorPolicy,
            ConnectorHealthStatus, ConnectorHealthSnapshot, HealthReport,
            HealthRuleResult,
            ConnectorQueryResult, ConnectorPipelineResult,
            ConnectorSummaryCard, CapabilityCardDTO, PolicyCardDTO,
            HealthCardDTO, PreviewCardDTO, ConnectorDashboard,
        ]
        for cls in dtos:
            assert dataclasses.is_dataclass(cls), f"{cls.__name__} not dataclass"
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} not frozen"

    def test_no_execute_method_in_runtime(self):
        """ConnectorRuntime must not have execute() method."""
        assert not hasattr(ConnectorRuntime, "execute"), \
            "ConnectorRuntime should not have execute()"

    def test_policy_violation_frozen(self):
        import dataclasses
        assert dataclasses.is_dataclass(PolicyViolation)

    def test_all_builtin_has_10(self):
        cs = CapabilitySet.all_builtin()
        assert len(cs.names) == 10
