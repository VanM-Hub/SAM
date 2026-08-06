"""REST API Wiring - Program J (RuntimeService Wiring).

Composition root untuk REST API host. Membangun jalur resmi `runtime_service.api`:
- RuntimeAPI + ExecutionRuntime (preview producer, mode=preview).
- ConversationPreviewGateway.
- 6 preview consumer (knowledge/workflow/artifact/memory/policy/audit).
- RESTApplication (host) dengan endpoint capability J3-J9 + status (J10).

Rewire J2 untuk /runtime dan /health dilakukan lewat `conversation_preview_gateway`
(gateway.api.status() / gateway.api.health()) - TIDAK import RuntimeCoordinator
langsung.

Pola mengikuti Program G/H/I (composition root di entry). TIDAK mengubah
RuntimeService. Endpoint HANYA memanggil jalur resmi (preview / status / health).
TIDAK ada business logic; RESTSerializer hanya memetakan hasil.
"""
from __future__ import annotations
from typing import Callable, Optional

from ..execution_runtime.execution_engine import ExecutionEngine
from ..execution_runtime.execution_request import ExecutionRequest
from ..execution_runtime.execution_runtime import ExecutionRuntime
from ..execution_runtime.execution_pipeline import ExecutionPipeline
from ..execution_runtime.provider_activation import ProviderActivationExecutor
from ..providers.execution.provider_executor import ProviderExecutor as RealProviderExecutor

from ..runtime_service.api import (
    RuntimeAPI,
    PreviewRequestView,
    wire_execution_preview,
    ConversationPreviewGateway,
)
from ..knowledge_runtime.foundation.knowledge_registry import KnowledgeRegistry
from ..workflow_runtime.foundation.workflow_registry import WorkflowRegistry
from ..artifact_runtime.foundation.artifact_registry import ArtifactRegistry
from ..memory.foundation.memory_registry import MemoryRegistry
from ..policy_runtime.foundation.policy_registry import PolicyRegistry
from ..audit_runtime.foundation.audit_registry import AuditRegistry

from ..runtime_service.api import (
    KnowledgePreviewConsumer,
    WorkflowPreviewConsumer,
    ArtifactPreviewConsumer,
    MemoryPreviewConsumer,
    PolicyPreviewConsumer,
    AuditPreviewConsumer,
)
from ..runtime_service.api.conversation_execution_builder import (
    ConversationExecutionContext,
)

from .presentation_rest import (
    RESTApplication,
    RESTRouter,
    RESTEndpoint,
    RESTSerializer,
)

# --------------------------------------------------------------------------- #
# Runtime API + ExecutionRuntime (preview producer) - composition root.
# Provider TIDAK dieksekusi (mode preview, ADR-024): external_calls=0.
# --------------------------------------------------------------------------- #
def _build_preview_request(view: PreviewRequestView):
    """Bangun ExecutionRequest(mode='preview'). Provider tidak dieksekusi."""
    return ExecutionRequest(
        execution_id=view.execution_id,
        provider_id=view.provider_id,
        operation=view.operation,
        mode="preview",  # preview-only (ADR-024); bukan execute
    )


def _execute_preview(request: ExecutionRequest):
    """Eksekusi preview via ExecutionRuntime (tidak execute nyata)."""
    return _execution_engine.execute(request)


runtime_api = RuntimeAPI()


def _build_runtime() -> None:
    """Bangun jalur preview RuntimeAPI -> ExecutionRuntime."""
    global _execution_engine
    _provider_executor = ProviderActivationExecutor(real=RealProviderExecutor())
    _provider_pipeline = ExecutionPipeline(executor=_provider_executor)
    _execution_engine = ExecutionEngine(
        runtime=ExecutionRuntime(pipeline=_provider_pipeline)
    )
    wire_execution_preview(
        runtime_api,
        build_request=_build_preview_request,
        execute=_execute_preview,
    )


_build_runtime()

# --------------------------------------------------------------------------- #
# ConversationPreviewGateway - jalur resmi capability preview.
# --------------------------------------------------------------------------- #
conversation_preview_gateway: ConversationPreviewGateway = ConversationPreviewGateway(
    runtime_api
)
conversation_preview_gateway.configure(provider_id="filesystem")

# --------------------------------------------------------------------------- #
# Registry + Consumer (data di-resolve via bridge, semua READ-ONLY preview).
# --------------------------------------------------------------------------- #
_knowledge_registry = KnowledgeRegistry()
knowledge_consumer: KnowledgePreviewConsumer = KnowledgePreviewConsumer(
    knowledgeregistry=_knowledge_registry,
)
_workflow_registry = WorkflowRegistry()
workflow_consumer: WorkflowPreviewConsumer = WorkflowPreviewConsumer(
    registry=_workflow_registry
)
_artifact_registry = ArtifactRegistry()
artifact_consumer: ArtifactPreviewConsumer = ArtifactPreviewConsumer(
    registry=_artifact_registry
)
_memory_registry = MemoryRegistry()
memory_consumer: MemoryPreviewConsumer = MemoryPreviewConsumer(
    registry=_memory_registry
)
_policy_registry = PolicyRegistry()
policy_consumer: PolicyPreviewConsumer = PolicyPreviewConsumer(
    registry=_policy_registry
)
_audit_registry = AuditRegistry()
audit_consumer: AuditPreviewConsumer = AuditPreviewConsumer(
    registry=_audit_registry
)


def _ctx() -> ConversationExecutionContext:
    """Context conversation default (preview). ID dari request handler."""
    return ConversationExecutionContext(
        conversation_id="rest-api",
        request="preview",
        turn_id="rest",
    )


def _resolve_ids(consumer: Callable[[], list], ids: list) -> Callable[[], dict]:
    """Factory handler list (READ-ONLY): daftar id capability."""
    def _handler() -> dict:
        return _serializer.serialize_many(ids, key_name="ids")
    return _handler


# Serializer (composition-only).
_serializer = RESTSerializer()


# --------------------------------------------------------------------------- #
# Endpoint capability J3-J9 + status (J10).
# Semua handler HANYA memanggil jalur resmi gateway / consumer.
# --------------------------------------------------------------------------- #
def _list_handler(ids_loader: Callable[[], list], key: str):
    def _handler():
        ids = ids_loader()
        return _serializer.serialize_many(ids, key_name=key)
    return _handler


def _resolve_handler(resolver):
    """Factory: resolve capability by id (READ-ONLY preview)."""
    def _handler(id: str):
        return _serializer.serialize(resolver(id))
    return _handler


def _preview_handler():
    """Preview umum (J6). mode=preview, tidak execute."""
    def _handler(execution_id: str, request: str = "preview"):
        result = conversation_preview_gateway.preview(
            context=ConversationExecutionContext(
                conversation_id="rest-api",
                request=request,
                turn_id=execution_id,
            ),
            execution_id=execution_id,
        )
        return _serializer.serialize(result)
    return _handler


def _approval_handler():
    """Approval pass-through (J9). Hanya baca field approved dari outcome.
    TIDAK membuat approval baru."""
    def _handler(execution_id: str):
        result = conversation_preview_gateway.preview(
            context=ConversationExecutionContext(
                conversation_id="rest-api",
                request="approval-check",
                turn_id=execution_id,
            ),
            execution_id=execution_id,
        )
        return {
            "approved": bool(getattr(result, "approved", False)),
            "executed": bool(getattr(result, "executed", False)),
            "mode": getattr(result, "mode", "preview"),
        }
    return _handler


def _status_handler():
    """Status runtime (J10). Jalur resmi: gateway.api.status()."""
    def _handler():
        status = conversation_preview_gateway.api.status()
        return _serializer.serialize(status)
    return _handler


_capability_router = RESTRouter(prefix="", tags=["capability"])

_capability_router.register_many([
    # workflow (J3)
    RESTEndpoint(path="/workflow/", tag="workflow",
                 handler=_list_handler(lambda: workflow_consumer.list_workflows(), "workflow_ids")),
    RESTEndpoint(path="/workflow/{id}", tag="workflow",
                 handler=_resolve_handler(workflow_consumer.resolve_workflow)),
    # policy (J4)
    RESTEndpoint(path="/policy/", tag="policy",
                 handler=_list_handler(lambda: policy_consumer.list_policies(), "policy_ids")),
    RESTEndpoint(path="/policy/{id}", tag="policy",
                 handler=_resolve_handler(policy_consumer.resolve_policy)),
    # audit (J5)
    RESTEndpoint(path="/audit/", tag="audit",
                 handler=_list_handler(lambda: audit_consumer.list_audits(), "audit_ids")),
    RESTEndpoint(path="/audit/{id}", tag="audit",
                 handler=_resolve_handler(audit_consumer.resolve_audit)),
    # preview (J6) - preview only
    RESTEndpoint(path="/preview/{execution_id}", tag="preview",
                 handler=_preview_handler()),
    # knowledge (J7)
    RESTEndpoint(path="/knowledge/", tag="knowledge",
                 handler=_list_handler(lambda: knowledge_consumer.list_knowledge(), "knowledge_ids")),
    RESTEndpoint(path="/knowledge/{id}", tag="knowledge",
                 handler=_resolve_handler(knowledge_consumer.resolve_knowledge)),
    # memory (J7)
    RESTEndpoint(path="/memory/", tag="memory",
                 handler=_list_handler(lambda: memory_consumer.list_memories(), "memory_ids")),
    RESTEndpoint(path="/memory/{id}", tag="memory",
                 handler=_resolve_handler(memory_consumer.resolve_memory)),
    # artifact (J8)
    RESTEndpoint(path="/artifact/", tag="artifact",
                 handler=_list_handler(lambda: artifact_consumer.list_artifacts(), "artifact_names")),
    RESTEndpoint(path="/artifact/{name}", tag="artifact",
                 handler=_resolve_handler(artifact_consumer.resolve_artifact)),
    # approval (J9) - pass-through
    RESTEndpoint(path="/approval/{execution_id}", tag="approval",
                 handler=_approval_handler()),
    # status (J10)
    RESTEndpoint(path="/status/", tag="status",
                 handler=_status_handler()),
])


# --------------------------------------------------------------------------- #
# RESTApplication - host REST API resmi (composition-only).
# --------------------------------------------------------------------------- #
rest_app = RESTApplication(
    title="SAM REST API",
    version="1.0",
    description="SAM REST API - Program J (Presentation Host). "
                "Seluruh endpoint melalui runtime_service.api.",
    routers=[_capability_router],
)
