"""Sprint 249 — Integration.

Program B — Model Runtime Integration.
Pipeline akhir: Mission->Agent->Workflow->Memory->Knowledge->Cognitive->
Policy->Audit->Artifact->Connector->Provider->Model Runtime->Execution Preview.
Semua bridge read-only.
"""
from __future__ import annotations
import pytest

from sam.model_runtime.runtime_registry import (
    RuntimeRegistry, RuntimeEntry, RUNTIME_PIPELINE_ORDER,
)
from sam.model_runtime.connector_bridge import ConnectorBridge, ConnectorBridgeView
from sam.model_runtime.provider_bridge import ProviderBridge, ProviderBridgeView
from sam.model_runtime.workflow_bridge import WorkflowBridge, WorkflowBridgeView
from sam.model_runtime.agent_bridge import AgentBridge, AgentBridgeView
from sam.model_runtime.model_integration import (
    ModelIntegration, ModelIntegrationResult, IntegrationStage,
)
from sam.model_runtime.model_descriptor import ModelDescriptor
from sam.model_runtime.model_request import ModelRequest
from sam.model_runtime.model_context import ModelContext
from sam.model_runtime.model_message import ModelMessage
from sam.model_runtime.conversation_integration import ConversationIntegration
from sam.model_runtime.dashboard_integration import DashboardIntegration


def test_pipeline_order_thirteen_stages():
    assert len(RUNTIME_PIPELINE_ORDER) == 13
    assert RUNTIME_PIPELINE_ORDER[0] == "mission"
    assert RUNTIME_PIPELINE_ORDER[-1] == "execution_preview"
    assert "model" in RUNTIME_PIPELINE_ORDER


def test_runtime_registry():
    reg = RuntimeRegistry()
    reg.register(RuntimeEntry(name="connector", kind="connector"))
    assert reg.entry("connector") is not None
    assert len(reg.order()) == 13
    reg.register_model_runtime(__import__("sam.model_runtime.model_runtime", fromlist=["ModelRuntime"]).ModelRuntime())
    assert reg.entry("model") is not None
    assert reg.model_runtime() is not None
    assert reg.certifier() is not None


def test_connector_bridge_readonly():
    from sam.connectors.connector_descriptor import ConnectorDescriptor
    desc = ConnectorDescriptor(connector_id="c1", name="fs-connector", connector_type="filesystem")
    view = ConnectorBridge().view(desc)
    assert isinstance(view, ConnectorBridgeView)
    assert view.connected is False
    assert view.external_calls == 0


def test_provider_bridge_known():
    pb = ProviderBridge()
    v = pb.view("anthropic", "claude-3")
    assert isinstance(v, ProviderBridgeView)
    assert v.provider == "anthropic"
    assert v.mode == "preview"
    assert v.external_calls == 0
    # fallback
    assert pb.view("ghost", "x").provider == "openai"


def test_workflow_bridge():
    v = WorkflowBridge().view("wf-1", steps_hint=4)
    assert isinstance(v, WorkflowBridgeView)
    assert v.external_calls == 0
    assert v.steps_hint == 4


def test_agent_bridge():
    v = AgentBridge().view("a1", ["chat"])
    assert isinstance(v, AgentBridgeView)
    assert v.capabilities == ["chat"]
    assert v.external_calls == 0


def make_req():
    return ModelRequest(
        request_id="r1", task="chat",
        context=ModelContext(messages=[ModelMessage(role="user", content="hi")]),
    )


def test_model_integration_pipeline():
    integ = ModelIntegration()
    desc = ModelDescriptor(id="m1", name="M", model_type="chat")
    result = integ.run(desc, make_req())
    assert isinstance(result, ModelIntegrationResult)
    assert result.preview_only is True
    assert result.external_calls == 0
    assert len(result.stages) == 13
    assert all(isinstance(s, IntegrationStage) for s in result.stages)
    names = [s.name for s in result.stages]
    assert names == list(RUNTIME_PIPELINE_ORDER)
    # pipeline method
    assert integ.pipeline() == list(RUNTIME_PIPELINE_ORDER)


def test_model_integration_certify():
    from sam.model_runtime.model_certifier import ModelCertifier
    from sam.model_runtime.model_manifest import ModelManifest
    from sam.model_runtime.model_contract import ModelContract
    from sam.model_runtime.model_metadata import ModelMetadata
    desc = ModelDescriptor(id="m1", name="M", model_type="chat")
    contract = ModelContract("c-m1", "m1", ["chat"], external_calls=0)
    meta = ModelMetadata(owner_id="m1", source_runtime="model", external_calls=0)
    manifest = ModelManifest("man-m1", desc, contract, meta)
    integ = ModelIntegration()
    report = integ.certify(manifest)
    assert report.passed is True


def test_conversation_integration_bridge():
    conv = ConversationIntegration()
    desc = ModelDescriptor(id="m1", name="M", model_type="chat")
    out = conv.run("conv-1", desc, make_req())
    assert out.external_calls == 0
    assert len(out.integration.stages) == 13


def test_dashboard_integration_rows():
    dash = DashboardIntegration()
    desc = ModelDescriptor(id="m1", name="M", model_type="chat")
    result = dash._integration.run(desc, make_req())
    dash.add(result)
    assert len(dash.rows()) == 1
    assert dash.rows()[0].stage_count == 13
    assert len(dash.pipeline()) == 13
    s = dash.summary()
    assert s["external_calls"] == 0


def test_no_forbidden_imports():
    import inspect
    import sam.model_runtime.model_integration as mi
    src = inspect.getsource(mi)
    for banned in ("import socket", "requests", "httpx", "asyncio",
                   "threading", "subprocess"):
        assert banned not in src
