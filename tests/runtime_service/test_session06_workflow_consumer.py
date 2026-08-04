"""Session 06 - Workflow & Automation Activation (AD-S06).

Workflow menjadi capability operasional yang aktif via activation path resmi.
Wire workflow consumer di entry pakai WorkflowRegistry + ConversationWorkflowBridge /
ConversationIntegrationBridge yg SUDAH ADA. Tanpa Scheduler/Planner/Automation baru;
tanpa ubah ExecutionRuntime/RuntimeService. Knowledge -> Workflow didukung.
"""
from __future__ import annotations
import inspect

import pytest

from sam.runtime_service.api import WorkflowPreviewConsumer, WorkflowPreview
from sam.workflow_runtime.foundation.workflow_registry import WorkflowRegistry
from sam.workflow_runtime.foundation.workflow_descriptor import WorkflowDescriptor


def _wreg() -> WorkflowRegistry:
    reg = WorkflowRegistry()
    reg.register(WorkflowDescriptor(
        id="wf-deploy", name="Deploy Pipeline", category="automation",
        description="Pipeline deploy", integrated_runtimes=["knowledge", "provider"]))
    reg.register(WorkflowDescriptor(
        id="wf-verify", name="Verify", category="quality"))
    return reg


@pytest.fixture
def consumer():
    return WorkflowPreviewConsumer(registry=_wreg())


def test_workflow_list(consumer):
    ids = consumer.list_workflows()
    assert "wf-deploy" in ids and "wf-verify" in ids


def test_workflow_resolve_found(consumer):
    wp = consumer.resolve_workflow("wf-deploy")
    assert isinstance(wp, WorkflowPreview)
    assert wp.found is True
    assert wp.name == "Deploy Pipeline"
    assert wp.category == "automation"
    assert wp.external_calls == 0


def test_workflow_resolve_unknown(consumer):
    wp = consumer.resolve_workflow("ghost")
    assert wp.found is False


def test_workflow_read_only_no_scheduler(consumer):
    wp = consumer.resolve_workflow("wf-deploy")
    assert wp.integration_ok is True
    assert wp.external_calls == 0
    assert wp.integrated_runtimes == ["knowledge", "provider"]
    # tidak ada scheduling/planning
    assert "scheduler" not in wp.as_dict()
    assert "plan" not in wp.as_dict()


def test_workflow_uses_existing_bridge():
    from sam.runtime_service.api import workflow_preview as wp
    src = inspect.getsource(wp)
    assert "ConversationWorkflowBridge" in src
    assert "ConversationIntegrationBridge" in src


def test_workflow_no_scheduler_planner_class(consumer):
    from sam.runtime_service.api import workflow_preview as wp
    src = inspect.getsource(wp)
    import_lines = [l for l in src.splitlines()
                    if l.strip().startswith(("import", "from", "class "))]
    joined = " ".join(import_lines)
    for banned in ("Scheduler", "Planner", "AutomationEngine", "Orchestrator"):
        assert banned not in joined, f"membangun komponen dilarang: {banned}"


def test_workflow_preview_immutable_no_execution(consumer):
    wp = consumer.resolve_workflow("wf-deploy")
    d = wp.as_dict()
    assert d["external_calls"] == 0
    assert "executed" not in d


def test_preview_with_workflow_via_conversation_path():
    """Conversation -> RuntimeService -> ExecutionRuntime -> Workflow (AD-S06)."""
    from sam.runtime_service.api import (
        RuntimeAPI,
        ConversationPreviewGateway,
        ConversationExecutionContext,
        KnowledgePreviewConsumer,
        wire_conversation_preview,
        PreviewRequestView,
    )
    from sam.execution_runtime.execution_engine import ExecutionEngine
    from sam.execution_runtime.execution_request import ExecutionRequest

    api = RuntimeAPI()
    engine = ExecutionEngine()

    def build(view: PreviewRequestView):
        return ExecutionRequest(
            execution_id=view.execution_id, provider_id=view.provider_id,
            operation=view.operation, mode="preview",
            payload={"conversation": {"conversation_id": "c", "request": "x"}},
        )

    wire_conversation_preview(api, build_request=build, execute=engine.execute)
    gw = ConversationPreviewGateway(api)
    wc = WorkflowPreviewConsumer(registry=_wreg())
    from sam.knowledge_runtime.foundation.knowledge_registry import KnowledgeRegistry
    kc = KnowledgePreviewConsumer(knowledgeregistry=KnowledgeRegistry())

    ctx = ConversationExecutionContext(conversation_id="s6", request="deploy", turn_id="t1")
    r = gw.preview_with_workflow(ctx, wc, "wf-deploy", "exec-6", kc)
    assert r["execution"]["executed"] is False
    assert r["execution"]["external_calls"] == 0
    assert r["workflow"]["found"] is True
    assert r["workflow"]["name"] == "Deploy Pipeline"
    assert r["workflow"]["external_calls"] == 0


def test_knowledge_flows_to_workflow():
    """Knowledge diteruskan ke Workflow sebagai input (INTEGRATION_ROUTE memuat knowledge)."""
    from sam.runtime_service.api import (
        RuntimeAPI,
        ConversationPreviewGateway,
        ConversationExecutionContext,
        KnowledgePreviewConsumer,
        wire_conversation_preview,
        PreviewRequestView,
    )
    from sam.execution_runtime.execution_engine import ExecutionEngine
    from sam.execution_runtime.execution_request import ExecutionRequest
    from sam.knowledge_runtime.foundation.knowledge_registry import KnowledgeRegistry
    from sam.knowledge_runtime.foundation.knowledge_descriptor import KnowledgeDescriptor

    api = RuntimeAPI()
    engine = ExecutionEngine()

    def build(view: PreviewRequestView):
        return ExecutionRequest(
            execution_id=view.execution_id, provider_id=view.provider_id,
            operation=view.operation, mode="preview", payload={})

    wire_conversation_preview(api, build_request=build, execute=engine.execute)
    gw = ConversationPreviewGateway(api)
    wc = WorkflowPreviewConsumer(registry=_wreg())
    kreg = KnowledgeRegistry()
    kreg.register(KnowledgeDescriptor(id="k-dep", name="Deploy Playbook", category="ops"))
    kc = KnowledgePreviewConsumer(knowledgeregistry=kreg)

    ctx = ConversationExecutionContext(conversation_id="s62", request="deploy")
    r = gw.preview_with_workflow(ctx, wc, "wf-deploy", "exec-62", kc, knowledge_id="k-dep")
    assert r["workflow"]["found"] is True
    assert r["knowledge"]["found"] is True
    assert r["knowledge"]["name"] == "Deploy Playbook"
