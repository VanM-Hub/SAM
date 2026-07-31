"""Sprint 259 - Integration.

Program C - Real Execution Runtime.
Pipeline akhir: Mission->Workflow->Policy->Memory->Knowledge->Cognitive->
Orchestrator->Connector->Provider->Model Runtime->Approval->Execution
Runtime->Artifact. Semua bridge read-only.
"""
from __future__ import annotations
import pytest

from sam.execution_runtime.execution_runtime_registry import (
    ExecutionRuntimeRegistry, RuntimeEntry, PIPELINE_ORDER,
)
from sam.execution_runtime.execution_descriptor import ExecutionDescriptor
from sam.execution_runtime.execution_request import ExecutionRequest
from sam.execution_runtime.execution_integration import (
    ExecutionIntegration, ExecutionIntegrationResult, IntegrationStage,
)
from sam.execution_runtime.conversation_execution_integration import (
    ConversationExecutionIntegration, ConversationExecutionIntegrationView,
)
from sam.execution_runtime.dashboard_execution_integration import DashboardExecutionIntegration


def test_pipeline_order_thirteen_stages():
    assert len(PIPELINE_ORDER) == 13
    assert PIPELINE_ORDER[0] == "mission"
    assert PIPELINE_ORDER[-1] == "artifact"
    assert "execution_runtime" in PIPELINE_ORDER
    assert "approval" in PIPELINE_ORDER


def test_runtime_registry():
    reg = ExecutionRuntimeRegistry()
    reg.register(RuntimeEntry(name="connector", kind="connector"))
    assert reg.entry("connector") is not None
    assert len(reg.order()) == 13
    from sam.execution_runtime.execution_runtime import ExecutionRuntime
    reg.register_execution_runtime(ExecutionRuntime())
    assert reg.entry("execution_runtime") is not None
    assert reg.execution_runtime() is not None
    assert reg.certifier() is not None


def test_runtime_entry_immutable():
    e = RuntimeEntry(name="policy")
    assert e.bridge == "read-only"
    assert e.external_calls == 0
    with pytest.raises(Exception):
        e.name = "x"


def make_descriptor():
    return ExecutionDescriptor(id="e1", name="Exec", operation="chat", mode="execute")


def make_req(mode="execute", approved=False):
    return ExecutionRequest(execution_id="e1", provider_id="openai", operation="chat",
                            mode=mode, approved=approved, approver="van" if approved else "")


def test_integration_preview_stages():
    integ = ExecutionIntegration()
    result = integ.run(ExecutionDescriptor(id="e1", name="E", operation="chat", mode="preview"),
                       make_req(mode="preview"))
    assert isinstance(result, ExecutionIntegrationResult)
    assert result.preview_only is True
    assert result.external_calls == 0
    assert result.outcome is None
    assert len(result.stages) == 13
    names = [s.name for s in result.stages]
    assert names == list(PIPELINE_ORDER)


def test_integration_execute_blocked_preview():
    # execute tanpa approval => tidak mengeksekusi, preview_only tetap True
    integ = ExecutionIntegration()
    result = integ.run(make_descriptor(), make_req(mode="execute", approved=False))
    assert result.outcome is None
    assert result.external_calls == 0
    assert result.preview_only is True


def test_integration_execute_approved_outcome():
    integ = ExecutionIntegration()
    result = integ.run(make_descriptor(), make_req(mode="execute", approved=True))
    # tanpa executor bound, eksekusi gagal (no provider executor bound) tapi dieksekusi=True
    assert result.preview_only is False
    assert result.outcome is not None
    assert result.outcome.executed is False  # handler tak ter-bound
    assert result.external_calls == 0


def test_integration_pipeline_method():
    integ = ExecutionIntegration()
    assert integ.pipeline() == list(PIPELINE_ORDER)


def test_integration_certify():
    integ = ExecutionIntegration()
    manifest = __import__("sam.execution_runtime.execution_certifier",
                          fromlist=["ExecutionCertifier"]).ExecutionCertifier().certify(
        __import__("sam.execution_runtime.execution_manifest", fromlist=["ExecutionManifest"]).ExecutionManifest(
            "m1",
            ExecutionDescriptor(id="e1", name="E", operation="x", mode="preview"),
            __import__("sam.execution_runtime.execution_contract", fromlist=["ExecutionContract"]).ExecutionContract("c", "e1"),
            __import__("sam.execution_runtime.execution_metadata", fromlist=["ExecutionMetadata"]).ExecutionMetadata(owner_id="e1"),
        ))
    assert manifest.passed is True


def test_conversation_integration_bridge():
    conv = ConversationExecutionIntegration()
    result = conv.run("conv-1", ExecutionDescriptor(id="e1", name="E", operation="chat", mode="preview"),
                      make_req(mode="preview"))
    assert isinstance(result, ConversationExecutionIntegrationView)
    assert result.external_calls == 0
    assert result.preview_only is True
    assert len(result.integration.stages) == 13


def test_dashboard_integration():
    dash = DashboardExecutionIntegration()
    result = dash._integration.run(
        ExecutionDescriptor(id="e1", name="E", operation="chat", mode="preview"),
        make_req(mode="preview"))
    dash.add(result)
    assert len(dash.rows()) == 1
    assert len(dash.pipeline()) == 13
    s = dash.summary()
    assert s["integrations"] == 1
    assert s["external_calls"] == 0


def test_all_stages_readonly_bridge():
    integ = ExecutionIntegration()
    result = integ.run(ExecutionDescriptor(id="e1", name="E", operation="chat", mode="preview"),
                       make_req(mode="preview"))
    assert all(s.bridge == "read-only" for s in result.stages)


def test_no_forbidden_imports_integration():
    import inspect
    import sam.execution_runtime.execution_integration as ei
    src = inspect.getsource(ei)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
