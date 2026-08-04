"""Conversation Preview Wiring (Session 02 - Conversation Capability).

Menghubungkan Conversation -> RuntimeAPI(execution.preview) -> ExecutionRuntime
(preview), REUSE PreviewGateway/ExecutionRuntime yang dibangun Session 01.

AD-S02-001: hanya namespace 'conversation' diisi di payload; tidak menambah
file DTO; tidak mengubah ExecutionRuntime/RuntimeService.
Pendekatan: wiring/komposisi di jalur entry (bukan di dalam RuntimeService),
dengan dependency injection — memakai builder ConversationExecutionRequestBuilder.

Alur:
  Conversation -> ConversationExecutionRequestBuilder.build(context)
  -> ExecutionRequest(mode='preview', payload={'conversation': {...}})
  -> RuntimeAPI(action='execution.preview') -> PreviewGateway -> ExecutionRuntime.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

from .request import APIRequest
from .runtime_api import RuntimeAPI
from .preview_gateway import PreviewGateway, PreviewRequestView
from .execution_preview_wiring import wire_execution_preview
from .conversation_execution_builder import (
    ConversationExecutionContext,
    ConversationExecutionRequestBuilder,
)
from .knowledge_preview import KnowledgePreviewConsumer
from .workflow_preview import WorkflowPreviewConsumer
from .artifact_preview import ArtifactPreviewConsumer


@dataclass(frozen=True)
class ConversationPreviewResult:
    """Hasil preview dari Conversation perspective (immutable)."""
    executed: bool = False
    approved: bool = False
    external_calls: int = 0
    mode: str = "preview"
    status: str = "preview"

    def as_dict(self) -> dict:
        return {
            "executed": self.executed,
            "approved": self.approved,
            "external_calls": self.external_calls,
            "mode": self.mode,
            "status": self.status,
        }


class ConversationPreviewGateway:
    """Gateway Conversation -> RuntimeService -> ExecutionRuntime preview.

    Penerima context conversation (immutable) dan mengirim Action preview via
    APIRequest(action='execution.preview'). Menggunakan builder utk membentuk
    ExecutionRequest(mode='preview') dengan payload namespace 'conversation'.
    """

    def __init__(self, api: RuntimeAPI) -> None:
        self._api = api
        self._builder = ConversationExecutionRequestBuilder()
        # provider default di-pass dari wiring (bukan logic di sini).
        # Gunakan provider yang dikenali KNOWN_PROVIDERS (preview tidak eksekusi).
        self._provider_id: str = "filesystem"
        self._operation: str = "conversation.preview"

    @property
    def api(self) -> RuntimeAPI:
        return self._api

    def configure(self, provider_id: str = "filesystem",
                  operation: str = "conversation.preview") -> None:
        self._provider_id = provider_id
        self._operation = operation

    def preview(self, context: ConversationExecutionContext,
                execution_id: str) -> ConversationPreviewResult:
        """Jalankan preview via RuntimeAPI(action='execution.preview')."""
        # BANGUN request sesuai desain (builder), lalu kirim lewat jalur resmi
        request = self._builder.build(
            context=context,
            provider_id=self._provider_id,
            operation=self._operation,
            execution_id=execution_id,
        )
        api_req = APIRequest(
            action="execution.preview",
            request_id=execution_id,
            payload={
                "execution_id": request.execution_id,
                "provider_id": request.provider_id,
                "operation": request.operation,
                "payload": request.payload,
            },
        )
        resp = self._api.handle(api_req)
        if not resp.is_ok():
            return ConversationPreviewResult(status="error")
        data = resp.data
        return ConversationPreviewResult(
            executed=bool(data.get("executed", False)),
            approved=bool(data.get("approved", False)),
            external_calls=int(data.get("external_calls", 0)),
            mode=str(data.get("mode", "preview")),
            status=str(data.get("status", "preview")),
        )

    def preview_with_knowledge(
        self,
        context: "ConversationExecutionContext",
        knowledge_consumer: KnowledgePreviewConsumer,
        knowledge_id: str,
        execution_id: str,
        memory_id: str = "",
    ) -> dict:
        """Conversation preview + Knowledge resolution via activation path.

        AD-S05 kombinasi A+B: Conversation->RuntimeService->ExecutionRuntime
        (preview) via `preview()`, lalu Knowledge di-resolve lewat bridge yang
        sudah ada (layer consumer, BUKAN pipeline). Memory di-resolve bila id
        diberikan & didukung. Tidak ada retriever/embedding/index baru.
        """
        result = self.preview(context, execution_id=execution_id)
        knowledge = knowledge_consumer.resolve_knowledge(knowledge_id)
        memory = knowledge_consumer.resolve_memory(memory_id) if memory_id else None
        return {
            "execution": result.as_dict(),
            "knowledge": knowledge.as_dict(),
            "memory": memory.as_dict() if memory is not None else None,
        }

    def preview_with_workflow(
        self,
        context: "ConversationExecutionContext",
        workflow_consumer: "WorkflowPreviewConsumer",
        workflow_id: str,
        execution_id: str,
        knowledge_consumer: "KnowledgePreviewConsumer",
        knowledge_id: str = "",
    ) -> dict:
        """Conversation preview + Workflow via activation path (AD-S06).

        Conversation->RuntimeService->ExecutionRuntime (preview) via preview(),
        lalu Workflow di-resolve lewat bridge yg sudah ada. Knowledge diteruskan
        ke Workflow sebagai input bila knowledge_id diberikan (knowledge ada di
        INTEGRATION_ROUTE workflow). Tanpa scheduler/planner/orchestration baru.
        """
        result = self.preview(context, execution_id=execution_id)
        workflow = workflow_consumer.resolve_workflow(workflow_id)
        knowledge = None
        if knowledge_id and knowledge_consumer is not None:
            knowledge = knowledge_consumer.resolve_knowledge(knowledge_id)
        return {
            "execution": result.as_dict(),
            "workflow": workflow.as_dict(),
            "knowledge": knowledge.as_dict() if knowledge is not None else None,
        }

    def preview_with_artifact(
        self,
        context: "ConversationExecutionContext",
        artifact_consumer: "ArtifactPreviewConsumer",
        artifact_name: str,
        execution_id: str,
    ) -> dict:
        """Conversation preview + Artifact via activation path (AD-S07).

        Conversation->RuntimeService->ExecutionRuntime (preview) via preview(),
        lalu Artifact di-resolve lewat bridge yg sudah ada (ArtifactRegistry ->
        ConversationArtifactBridge -> ConversationIntegrationBridge).
        Pattern Standard AD-ENG-002. Tanpa generate/engine/architecture baru;
        tanpa integrasi Mission/Contract/Dashboard/Intelligence.
        """
        result = self.preview(context, execution_id=execution_id)
        artifact = artifact_consumer.resolve_artifact(artifact_name)
        return {
            "execution": result.as_dict(),
            "artifact": artifact.as_dict(),
        }



def wire_conversation_preview(api: RuntimeAPI,
                              build_request: Callable[[PreviewRequestView], object],
                              execute: Callable[[object], object]) -> PreviewGateway:
    """Wiring Conversation -> RuntimeAPI -> ExecutionRuntime preview.

    Menerima build_request/execute (dependency injection) yang sudah mengikat
    ke ExecutionEngine. Menghasilkan PreviewGateway + ConversationPreviewGateway
    (melalui 2 objek yang berbagi RuntimeAPI yang sama).
    """
    gateway = wire_execution_preview(
        api,
        build_request=build_request,
        execute=execute,
    )
    return gateway


def build_conversation_preview_gateway(api: RuntimeAPI) -> ConversationPreviewGateway:
    """Buat ConversationPreviewGateway di atas RuntimeAPI (tanpa execution wiring)."""
    return ConversationPreviewGateway(api)
