"""Memory Preview Consumer (Session 08 - Memory Runtime Activation).

AD-ENG-002 Activation Pattern Standard:
  Conversation -> RuntimeService -> ExecutionRuntime(preview)
  -> MemoryPreviewConsumer -> MemoryRegistry -> ConversationMemoryBridge -> STOP.

Wire Memory di entry via jalur resmi, pakai MemoryRegistry + ConversationMemoryBridge +
ConversationIntegrationBridge yang SUDAH ADA. MEMORY MENJADI CAPABILITY MANDIRI
(bukan lagi namespace payload — payload tetap, tapi bukan consumer). AD-S08.

Tanpa MemoryEngine/Storage/DB/Embedding/Retrieval/Runtime baru; tanpa ubah
ExecutionRuntime/RuntimeService/internal memory. Tanpa integrasi pengetahuan/workflow.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sam.memory.foundation.memory_registry import MemoryRegistry
from sam.memory.foundation.conversation_memory import ConversationMemoryBridge
from sam.memory.integration.conversation_integration import (
    ConversationIntegrationBridge,
)


@dataclass(frozen=True)
class MemoryContextPreview:
    """Snapshot memory (immutable, read-only). Preview-only, no storage/retrieval.
    Dinamai MemoryContextPreview utk menghindari konflik dgn MemoryPreview pasif
    di knowledge_preview (S05). S08 = Memory capability mandiri (AD-ENG-002)."""
    memory_id: str
    found: bool = False
    name: str = ""
    category: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    integration_ok: bool = False
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "memory_id": self.memory_id,
            "found": self.found,
            "name": self.name,
            "category": self.category,
            "metadata": dict(self.metadata),
            "capabilities": list(self.capabilities),
            "integration_ok": self.integration_ok,
            "external_calls": self.external_calls,
        }


class MemoryPreviewConsumer:
    """Consumer Memory via jalur Conversation -> RuntimeService.

    READ-ONLY: resolve memory dari registry (yang sudah ada), via bridge.
    Memory jadi capability mandiri (bukan lagi hanya hook pasif di knowledge).
    BUKAN pipeline internal; tidak mengubah ExecutionRuntime/RuntimeService.
    Tidak menghubungkan knowledge/workflow/mission/intelligence.
    """

    def __init__(self, registry: Optional[MemoryRegistry] = None) -> None:
        self._registry = registry or MemoryRegistry()
        self._bridge = ConversationMemoryBridge(self._registry)
        self._integ = ConversationIntegrationBridge(self._registry)

    @property
    def registry(self) -> MemoryRegistry:
        return self._registry

    def list_memories(self) -> List[str]:
        """Daftar id memory (read-only)."""
        return self._registry.list_ids()

    def resolve_memory(self, memory_id: str) -> MemoryContextPreview:
        """Resolve satu memory via bridge (read-only, no storage/retrieval)."""
        if not self._registry.exists(memory_id):
            return MemoryContextPreview(memory_id=memory_id, found=False)
        d = self._registry.find(memory_id)
        run = self._integ.query_3_pipeline(memory_id)
        return MemoryContextPreview(
            memory_id=memory_id,
            found=True,
            name=d.name,
            category=d.category,
            metadata=self._bridge.query_4_metadata(memory_id),
            capabilities=self._bridge.query_5_capability(memory_id),
            integration_ok=bool(run.get("ok")),
            external_calls=0,
        )

    def summary(self) -> dict:
        """Ringkasan memory registry (read-only)."""
        return {
            "total_memories": self._registry.count(),
            "ids": self._registry.list_ids(),
        }
