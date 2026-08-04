"""Workflow Preview Consumer (Session 06 - Workflow & Automation).

AD-S06 (pola konsisten S05): Wire workflow consumer di entry via jalur resmi,
pakai WorkflowRegistry + ConversationWorkflowBridge / ConversationIntegrationBridge
yang SUDAH ADA. Tanpa WorkflowRuntime/Scheduler/Planner/Automation baru; tanpa ubah
ExecutionRuntime/RuntimeService/internal workflow_runtime.

Alur:
  Conversation -> ConversationPreviewGateway -> ExecutionRequest(mode='preview')
  -> RuntimeAPI('execution.preview') -> ExecutionRuntime (preview)
  -> WorkflowPreview resolve via registry/bridge (layanan consumer, BUKAN pipeline).

Preview-only: summary/status/pipeline (baca). TIDAK scheduling/planner/orchestration.
Knowledge -> Workflow didukung (INTEGRATION_ROUTE workflow memuat 'knowledge').
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from sam.workflow_runtime.foundation.workflow_registry import WorkflowRegistry
from sam.workflow_runtime.foundation.conversation_workflow import (
    ConversationWorkflowBridge,
)
from sam.workflow_runtime.integration.conversation_integration import (
    ConversationIntegrationBridge,
)


@dataclass(frozen=True)
class WorkflowPreview:
    """Snapshot workflow (immutable, read-only). Tidak ada scheduling/planning."""
    workflow_id: str
    found: bool = False
    name: str = ""
    category: str = ""
    description: str = ""
    integrated_runtimes: List[str] = field(default_factory=list)
    status: str = ""
    integration_ok: bool = False
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "found": self.found,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "integrated_runtimes": list(self.integrated_runtimes),
            "status": self.status,
            "integration_ok": self.integration_ok,
            "external_calls": self.external_calls,
        }


class WorkflowPreviewConsumer:
    """Consumer Workflow via jalur Conversation -> RuntimeService.

    Membaca workflow dari registry (yang sudah ada), resolve via bridge.
    BUKAN pipeline internal; tidak mengubah ExecutionRuntime/RuntimeService.
    Bisa membawa knowledge sbg input bila workflow mereferensikannya.
    """

    def __init__(self, registry: Optional[WorkflowRegistry] = None) -> None:
        self._registry = registry or WorkflowRegistry()
        self._bridge = ConversationWorkflowBridge(self._registry)
        self._integ = ConversationIntegrationBridge(self._registry)

    @property
    def registry(self) -> WorkflowRegistry:
        return self._registry

    def list_workflows(self) -> List[str]:
        """Daftar id workflow (read-only)."""
        return [d.id for d in self._registry.all()]

    def resolve_workflow(self, workflow_id: str) -> WorkflowPreview:
        """Resolve satu workflow via bridge (read-only, no scheduling/planning)."""
        if not self._registry.exists(workflow_id):
            return WorkflowPreview(workflow_id=workflow_id, found=False)
        d = self._registry.get(workflow_id)
        status = self._bridge.status(workflow_id)
        run = self._integ.query_3_pipeline(workflow_id)
        return WorkflowPreview(
            workflow_id=workflow_id,
            found=True,
            name=d.name,
            category=d.category,
            description=d.description,
            integrated_runtimes=list(d.integrated_runtimes),
            status=status,
            integration_ok=bool(run.get("ok")),
            external_calls=0,
        )

    def summary(self) -> dict:
        """Ringkasan workflow registry (read-only)."""
        return self._bridge.summary()
