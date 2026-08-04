"""Session 08 - Memory Runtime Activation (AD-ENG-002 Pattern Standard).

Memory menjadi capability operasional MANDIRI (bukan lagi hanya namespace payload
atau hook pasif S05). Conversation -> RuntimeService -> ExecutionRuntime(preview) ->
MemoryPreviewConsumer -> MemoryRegistry -> ConversationMemoryBridge -> STOP.

Tanpa MemoryEngine/Storage/DB/Embedding/Retrieval/Runtime baru; tanpa integrasi
knowledge/workflow/mission/intelligence; tanpa ubah ExecutionRuntime/RuntimeService.
"""
from __future__ import annotations
import inspect

import pytest

from sam.runtime_service.api import MemoryPreviewConsumer, MemoryContextPreview
from sam.memory.foundation.memory_registry import MemoryRegistry
from sam.memory.foundation.memory_descriptor import MemoryDescriptor


def _mreg() -> MemoryRegistry:
    reg = MemoryRegistry()
    reg.register(MemoryDescriptor(id="mem-session", name="Session Memory",
                                  category="session"))
    reg.register(MemoryDescriptor(id="mem-mission", name="Mission Memory",
                                  category="mission"))
    return reg


@pytest.fixture
def consumer():
    return MemoryPreviewConsumer(registry=_mreg())


def test_memory_list(consumer):
    ids = consumer.list_memories()
    assert "mem-session" in ids and "mem-mission" in ids


def test_memory_resolve_found(consumer):
    mp = consumer.resolve_memory("mem-session")
    assert isinstance(mp, MemoryContextPreview)
    assert mp.found is True
    assert mp.name == "Session Memory"
    assert mp.external_calls == 0


def test_memory_resolve_unknown(consumer):
    mp = consumer.resolve_memory("ghost")
    assert mp.found is False


def test_memory_preview_no_storage_retrieval(consumer):
    mp = consumer.resolve_memory("mem-session")
    assert mp.integration_ok is True
    assert mp.external_calls == 0
    d = mp.as_dict()
    assert "executed" not in d
    assert "retrieved" not in d
    assert "stored" not in d


def test_memory_uses_existing_bridge():
    from sam.runtime_service.api import memory_preview as mp
    src = inspect.getsource(mp)
    assert "ConversationMemoryBridge" in src
    assert "ConversationIntegrationBridge" in src


def test_memory_no_knowledge_workflow_integration():
    from sam.runtime_service.api import memory_preview as mod
    src = inspect.getsource(mod)
    import_lines = [l for l in src.splitlines()
                    if l.strip().startswith(("import", "from"))]
    joined = " ".join(import_lines).lower()
    for banned in ("knowledge", "workflow", "artifact", "intelligence", "mission"):
        assert banned not in joined, f"memory terhubung ke {banned}"


def test_memory_no_engine_storage(consumer):
    from sam.runtime_service.api import memory_preview as mp
    src = inspect.getsource(mp)
    import_lines = [l for l in src.splitlines()
                    if l.strip().startswith(("import", "from"))]
    joined = " ".join(import_lines)
    for banned in ("MemoryEngine", "Storage", "VectorDB", "Embedding", "Retriever"):
        assert banned not in joined, f"memory membangun {banned}"


def test_memory_independent_from_payload_namespace():
    """Memory = capability mandiri (memiliki sendiri consumer), bukan cuma namespace."""
    consumer_cls = MemoryPreviewConsumer(registry=_mreg())
    mp = consumer_cls.resolve_memory("mem-mission")
    assert mp.found is True
    assert mp.name == "Mission Memory"


def test_preview_with_memory_via_conversation_path():
    """Conversation -> RuntimeService -> ExecutionRuntime -> Memory (AD-ENG-002)."""
    from sam.runtime_service.api import (
        RuntimeAPI,
        ConversationPreviewGateway,
        ConversationExecutionContext,
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
    mc = MemoryPreviewConsumer(registry=_mreg())
    ctx = ConversationExecutionContext(conversation_id="s8", request="ingat konteks")
    r = gw.preview_with_memory(ctx, mc, "mem-session", "exec-8")
    assert r["execution"]["executed"] is False
    assert r["execution"]["external_calls"] == 0
    assert r["memory"]["found"] is True
    assert r["memory"]["name"] == "Session Memory"
    assert r["memory"]["external_calls"] == 0
