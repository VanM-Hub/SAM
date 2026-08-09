"""Test IP-5.2-002..005 - Connector, Governed Execution, Workspace, Certification.

Coverage: WP-11..WP-50.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.universal_tool import (
    CapabilityBinder,
    ConnectorAPI,
    ConnectorComplianceChecker,
    ConnectorHandle,
    ConnectorState,
    ConnectorType,
    CredentialBinder,
    ExecutionStage,
    GovernedToolInvoker,
    ToolAuditLog,
    ToolCapabilityKind,
    ToolCertification,
    ToolCertStatus,
    ToolConnector,
    ToolExplainer,
    ToolExecutionComplianceChecker,
    ToolResponse,
    ToolResultState,
    ToolResultVerifier,
    ToolWorkspace,
    WorkspaceComplianceChecker,
)


def _connector(cid="conn-1", tool_id="tool-1", transport=None):
    handle = ConnectorHandle(connector_id=cid, tool_id=tool_id, connector_type=ConnectorType.HTTP_API)
    return ToolConnector(handle=handle, transport=transport)


# ---------------------------------------------------------------------------
# WP-11..16 Connector
# ---------------------------------------------------------------------------

class TestConnector:
    def test_connector_mock_call(self):
        connector = _connector()
        result = connector.call({"action": "get"})
        assert result["_mock"] is True

    def test_transport_call(self):
        connector = _connector(transport=lambda r: {"ok": True, "data": r})
        assert connector.call({"a": 1})["data"] == {"a": 1}

    def test_credential_binding_no_secret(self):
        connector = _connector()
        connector.bind_credential("ref-1")
        assert connector.credential_ref == "ref-1"
        binder = CredentialBinder()
        binding = binder.bind("conn-1", "ref-1")
        assert binder.never_exposes_secret(binding) is True

    def test_capability_binding(self):
        binder = CapabilityBinder()
        binder.bind("conn-1", (ToolCapabilityKind.READ,))
        assert binder.binding_for("conn-1").supports(ToolCapabilityKind.READ) is True
        assert binder.connectors_for(ToolCapabilityKind.WRITE) == ()


# ---------------------------------------------------------------------------
# WP-17/18 Connector API
# ---------------------------------------------------------------------------

class TestConnectorAPI:
    def test_connect_view_health(self):
        api = ConnectorAPI()
        connector = _connector()
        api.register(connector)
        api.connect("conn-1")
        assert api.view("conn-1").state == ConnectorState.CONNECTED
        assert api.health("conn-1").healthy is True
        assert api.connector_type_available(ConnectorType.HTTP_API) is True

    def test_missing_view(self):
        assert ConnectorAPI().view("x") is None


# ---------------------------------------------------------------------------
# WP-19 Connector Compliance
# ---------------------------------------------------------------------------

class TestConnectorCompliance:
    def test_certify_passes(self):
        assert ConnectorComplianceChecker().certify((_connector(),))["certified"] is True

    def test_fails_on_sdk_leak(self):
        assert ConnectorComplianceChecker().certify((_connector(),), no_sdk_leak=False)["certified"] is False


# ---------------------------------------------------------------------------
# WP-23/24 Governed Tool Invocation
# ---------------------------------------------------------------------------

class TestGovernedInvocation:
    def test_execution_requires_approval(self):
        invoker = GovernedToolInvoker()
        ctx = invoker.execute(
            request_id="r1", tool_id="tool-1", connector_id="conn-1",
            capability="read", require_approval=True, approved=True,
        )
        assert ctx.approved is True
        assert ctx.all_passed is True
        stages = [d.stage for d in ctx.decisions]
        assert ExecutionStage.EXECUTION in stages

    def test_blocks_without_approval(self):
        invoker = GovernedToolInvoker()
        ctx = invoker.execute(
            request_id="r1", tool_id="tool-1", connector_id="conn-1",
            capability="read", require_approval=True, approved=False,
        )
        assert ctx.all_passed is False
        last = ctx.decisions[-1]
        assert last.stage == ExecutionStage.EXECUTION and last.passed is False

    def test_no_approval_required(self):
        invoker = GovernedToolInvoker()
        ctx = invoker.execute(
            request_id="r1", tool_id="tool-1", connector_id="conn-1",
            capability="read", require_approval=False,
        )
        assert ctx.all_passed is True


# ---------------------------------------------------------------------------
# WP-25/26 Response & Verification
# ---------------------------------------------------------------------------

class TestToolResponse:
    def test_success_and_verify(self):
        resp = ToolResponse(request_id="r1", tool_id="tool-1", state=ToolResultState.SUCCESS, data={"x": 1})
        assert resp.successful is True
        assert ToolResultVerifier().verify(resp, expected_keys=("x",)) is True
        assert ToolResultVerifier().verify(resp, expected_keys=("y",)) is False


# ---------------------------------------------------------------------------
# WP-27/28 Audit & Explainability
# ---------------------------------------------------------------------------

class TestToolAudit:
    def test_audit_records(self):
        invoker = GovernedToolInvoker()
        ctx = invoker.execute(request_id="r1", tool_id="tool-1", connector_id="conn-1", capability="read")
        log = ToolAuditLog()
        log.record(ctx)
        assert len(log.entries()) == 1
        assert log.entries()[0].executed is True
        explanation = ToolExplainer().explain(ctx)
        assert "governance_path" in explanation


# ---------------------------------------------------------------------------
# WP-29 Execution Compliance
# ---------------------------------------------------------------------------

class TestExecutionCompliance:
    def test_certify_after_approval(self):
        invoker = GovernedToolInvoker()
        ctx = invoker.execute(request_id="r1", tool_id="tool-1", connector_id="conn-1", capability="read", approved=True)
        assert ToolExecutionComplianceChecker().certify(ctx)["certified"] is True

    def test_bypass_detected(self):
        # Execution yang nilainya bypass governance terdeteksi oleh checker
        invoker = GovernedToolInvoker()
        ctx = invoker.execute(request_id="r1", tool_id="tool-1", connector_id="conn-1",
                              capability="read", approved=True)
        assert ctx.all_passed is True
        # No bypass: alur governance diikuti -> aman
        assert ToolExecutionComplianceChecker().certify(ctx)["certified"] is True
        # Bypass eksplisit -> harus gagal
        assert ToolExecutionComplianceChecker().certify(ctx, no_bypass=False)["certified"] is False


# ---------------------------------------------------------------------------
# WP-31..40 Workspace
# ---------------------------------------------------------------------------

class TestWorkspace:
    def test_execution_history_and_investigation(self):
        workspace = ToolWorkspace()
        log = workspace.audit
        invoker = GovernedToolInvoker()
        log.record(invoker.execute(request_id="r1", tool_id="tool-1", connector_id="conn-1", capability="read"))
        assert len(workspace.execution_history("tool-1")) == 1
        inv = workspace.investigate("tool-1")
        assert "executed=1" in inv.findings
        ctx = workspace.operational_context("tool-1")
        assert ctx.health is not None

    def test_workspace_compliance(self):
        assert WorkspaceComplianceChecker().certify()["certified"] is True
        assert WorkspaceComplianceChecker().certify(no_execution=False)["certified"] is False


# ---------------------------------------------------------------------------
# WP-41..50 Tool Certification
# ---------------------------------------------------------------------------

class TestToolCertification:
    def test_full_certified(self):
        cert = ToolCertification()
        cert.contract_certification()
        cert.connector_certification()
        cert.capability_certification()
        cert.execution_certification()
        cert.security_verification()
        cert.governance_verification()
        cert.audit_verification()
        cert.regression_verification()
        cert.production_readiness()
        cert.mission_certification()
        result = cert.certify()
        assert result["certified"] is True
        assert result["status"] == ToolCertStatus.CERTIFIED.value

    def test_not_certified(self):
        cert = ToolCertification()
        cert.security_verification(credential_isolated=False, no_secret=False)
        cert.governance_verification(no_tool_authority=False)
        assert cert.certify()["status"] == ToolCertStatus.NOT_CERTIFIED.value
