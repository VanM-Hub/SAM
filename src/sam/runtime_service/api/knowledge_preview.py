"""Knowledge Preview Consumer (Session 05 - Knowledge & Memory Activation).

AD-S05 (kombinasi A+B):
- A: Wire Knowledge consumer di entry (jalur resmi), pakai KnowledgeRegistry +
  ConversationKnowledgeBridge / ConversationIntegrationBridge yang SUDAH ADA.
  Tanpa mengubah ExecutionRuntime/RuntimeService/internal knowledge_runtime.
- B: Pakai AD-S02-001 namespace — ExecutionRequest.payload['knowledge'] mulai
  diisi saat Conversation minta knowledge; 'memory' bila didukung.

Alur:
  Conversation -> ConversationPreviewGateway -> ExecutionRequest(mode='preview',
  payload={'conversation':..., 'knowledge': {...}})
  -> RuntimeAPI('execution.preview') -> ExecutionRuntime (preview)
  -> KnowledgePreview resolve via registry/bridge (layanan consumer, BUKAN pipeline).

Preview-only: summary/list/descriptor/metadata/capability (baca). TIDAK
Indexing/Embedding/Search/RAG/Retrieval (dilarang AD-S05).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sam.knowledge_runtime.foundation.knowledge_registry import KnowledgeRegistry
from sam.knowledge_runtime.foundation.conversation_knowledge import (
    ConversationKnowledgeBridge,
)
from sam.knowledge_runtime.integration.conversation_integration import (
    ConversationIntegrationBridge,
)
from sam.memory.foundation.conversation_memory import ConversationMemoryBridge
from sam.memory.foundation.memory_registry import MemoryRegistry


@dataclass(frozen=True)
class KnowledgePreview:
    """Snapshot knowledge (immutable, read-only). Tidak ada inference/index."""
    knowledge_id: str
    found: bool = False
    name: str = ""
    category: str = ""
    summary: Dict[str, Any] = field(default_factory=dict)
    descriptor: Optional[dict] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    integration_ok: bool = False
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "knowledge_id": self.knowledge_id,
            "found": self.found,
            "name": self.name,
            "category": self.category,
            "summary": dict(self.summary),
            "descriptor": self.descriptor,
            "metadata": dict(self.metadata),
            "capabilities": list(self.capabilities),
            "integration_ok": self.integration_ok,
            "external_calls": self.external_calls,
        }


@dataclass(frozen=True)
class MemoryPreview:
    """Snapshot memory context (immutable). Bila Memory didukung repository."""
    memory_id: str
    found: bool = False
    name: str = ""
    summary: Dict[str, Any] = field(default_factory=dict)
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "memory_id": self.memory_id,
            "found": self.found,
            "name": self.name,
            "summary": dict(self.summary),
            "external_calls": self.external_calls,
        }


class KnowledgePreviewConsumer:
    """Consumer Knowledge untuk jalur Conversation -> RuntimeService.

    Membaca namespace 'knowledge' (dan 'memory' bila didukung) dari payload
    ExecutionRequest, lalu me-resolve lewat registry/bridge yang sudah ada.
    BUKAN pipeline internal; tidak mengubah ExecutionRuntime/RuntimeService.
    """

    def __init__(self,
                 knowledgeregistry: Optional[KnowledgeRegistry] = None,
                 memory_registry: Optional[MemoryRegistry] = None) -> None:
        self._kreg = knowledgeregistry or KnowledgeRegistry()
        self._mreg = memory_registry  # optional (conditional, AD-S05)
        self._kbridge = ConversationKnowledgeBridge(self._kreg)
        self._kinteg = ConversationIntegrationBridge(self._kreg)

    @property
    def registry(self) -> KnowledgeRegistry:
        return self._kreg

    def resolve_knowledge(self, knowledge_id: str) -> KnowledgePreview:
        """Resolve satu knowledge via bridge (read-only, no index/embed)."""
        found = self._kreg.exists(knowledge_id)
        if not found:
            return KnowledgePreview(knowledge_id=knowledge_id, found=False)
        d = self._kreg.find(knowledge_id)
        summary = self._kbridge.query_1_summary()
        # pipeline preview integrasi (read-only)
        run = self._kinteg.query_3_pipeline(knowledge_id)
        return KnowledgePreview(
            knowledge_id=knowledge_id,
            found=True,
            name=d.name,
            category=d.category,
            summary=summary,
            descriptor={"id": d.id, "name": d.name, "version": d.version,
                        "category": d.category, "description": d.description},
            metadata=self._kbridge.query_4_metadata(knowledge_id),
            capabilities=self._kbridge.query_5_capability(knowledge_id),
            integration_ok=bool(run.get("ok")),
            external_calls=0,
        )

    def list_knowledge(self) -> List[str]:
        """Daftar id knowledge (read-only)."""
        return self._kreg.list_ids()

    def resolve_memory(self, memory_id: str) -> MemoryPreview:
        """Memory context bila repository mendukung (conditional)."""
        if self._mreg is None:
            return MemoryPreview(memory_id=memory_id, found=False)
        if not self._mreg.exists(memory_id):
            return MemoryPreview(memory_id=memory_id, found=False)
        mbridge = ConversationMemoryBridge(self._mreg)
        m = self._mreg.find(memory_id)
        return MemoryPreview(
            memory_id=memory_id,
            found=True,
            name=m.name,
            summary=mbridge.query_1_summary(),
            external_calls=0,
        )

    def has_memory_support(self) -> bool:
        return self._mreg is not None
