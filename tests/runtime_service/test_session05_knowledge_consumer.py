"""Session 05 - Knowledge & Memory Activation (AD-S05, kombinasi A+B).

Knowledge menjadi capability pertama yang aktif via activation path resmi SAM.
A: konsumer Knowledge di entry (library bridge yg sudah ada).
B: namespace 'knowledge'/'memory' di payload (AD-S02-001 forward compat).
Tanpa retriever/embedding/index/RAG/reasoning baru; tanpa ubah ExecutionRuntime.
"""
from __future__ import annotations
import inspect

import pytest

from sam.runtime_service.api import KnowledgePreviewConsumer, KnowledgePreview
from sam.knowledge_runtime.foundation.knowledge_registry import KnowledgeRegistry
from sam.knowledge_runtime.foundation.knowledge_descriptor import KnowledgeDescriptor
from sam.knowledge_runtime.foundation.knowledge_contract import KnowledgeContract


def _kreg() -> KnowledgeRegistry:
    reg = KnowledgeRegistry()
    reg.register(KnowledgeDescriptor(
        id="k-ops", name="Ops Playbook", category="operations",
        description="Runbook operasional"))
    reg.register(KnowledgeDescriptor(
        id="k-sec", name="Security Policy", category="security"))
    reg.attach_contract(KnowledgeContract(
        contract_id="c1", knowledge_id="k-ops", name="ops-contract"))
    return reg


@pytest.fixture
def consumer():
    return KnowledgePreviewConsumer(knowledgeregistry=_kreg())


def test_knowledge_list(consumer):
    ids = consumer.list_knowledge()
    assert "k-ops" in ids and "k-sec" in ids


def test_knowledge_resolve_found(consumer):
    kp = consumer.resolve_knowledge("k-ops")
    assert isinstance(kp, KnowledgePreview)
    assert kp.found is True
    assert kp.name == "Ops Playbook"
    assert kp.category == "operations"
    assert kp.external_calls == 0


def test_knowledge_resolve_unknown(consumer):
    kp = consumer.resolve_knowledge("ghost")
    assert kp.found is False


def test_knowledge_resolve_read_only_no_inference(consumer):
    kp = consumer.resolve_knowledge("k-ops")
    # tidak ada inference/search/RAG — hanya metadata & pipeline preview
    assert kp.integration_ok is True
    assert kp.external_calls == 0
    assert kp.descriptor["id"] == "k-ops"


def test_knowledge_no_index_embed_retriever(consumer):
    """Consumer TIDAK membangun indexing/embedding/retriever (resolve-only)."""
    from sam.runtime_service.api import knowledge_preview as kp
    src = inspect.getsource(kp)
    # periksa baris import & definisi class (bukan docstring)
    code_lines = [l for l in src.splitlines()
                  if l.strip().startswith(("import", "from", "class "))]
    joined = " ".join(code_lines)
    for banned in ("VectorStore", "Embedding", "Retriever", "Indexer",
                   "FAISS", "ANN"):
        assert banned not in joined, f"module membangun {banned}"


def test_knowledge_uses_existing_bridge():
    """Consumer memakai ConversationKnowledgeBridge/Integration yg ADA (A)."""
    import sam.runtime_service.api.knowledge_preview as kp
    src = inspect.getsource(kp)
    assert "ConversationKnowledgeBridge" in src
    assert "ConversationIntegrationBridge" in src


def test_memory_conditional_support(consumer):
    # tanpa memory_registry -> tidak didukung
    assert consumer.has_memory_support() is False
    mp = consumer.resolve_memory("mem-1")
    assert mp.found is False


def test_memory_with_registry():
    from sam.memory.foundation.memory_registry import MemoryRegistry
    from sam.memory.foundation.memory_descriptor import MemoryDescriptor
    mreg = MemoryRegistry()
    mreg.register(MemoryDescriptor(id="mem-1", name="Session Memory"))
    c = KnowledgePreviewConsumer(knowledgeregistry=_kreg(), memory_registry=mreg)
    assert c.has_memory_support() is True
    mp = c.resolve_memory("mem-1")
    assert mp.found is True
    assert mp.name == "Session Memory"
    assert mp.external_calls == 0


def test_preview_immutable_no_execution():
    """Knowledge preview tidak pernah execute (preview-only)."""
    consumer_cls = KnowledgePreviewConsumer(knowledgeregistry=_kreg())
    kp = consumer_cls.resolve_knowledge("k-ops")
    d = kp.as_dict()
    assert d["external_calls"] == 0
    assert "executed" not in d  # bukan result eksekusi


def test_preview_with_knowledge_via_conversation_path():
    """Conversation -> RuntimeService -> ExecutionRuntime -> Knowledge (A+B)."""
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
            execution_id=view.execution_id,
            provider_id=view.provider_id,
            operation=view.operation,
            mode="preview",
            payload={"conversation": {"conversation_id": "c", "request": "x"}},
        )

    wire_conversation_preview(api, build_request=build, execute=engine.execute)
    gw = ConversationPreviewGateway(api)
    kc = KnowledgePreviewConsumer(knowledgeregistry=_kreg())

    ctx = ConversationExecutionContext(
        conversation_id="s5", request="Apa runbook?", turn_id="t1")
    r = gw.preview_with_knowledge(
        ctx, kc, knowledge_id="k-ops", execution_id="exec-5")
    # execution preview berjalan (provider tidak dieksekusi)
    assert r["execution"]["executed"] is False
    assert r["execution"]["external_calls"] == 0
    # knowledge di-resolve via jalur Conversation
    assert r["knowledge"]["found"] is True
    assert r["knowledge"]["name"] == "Ops Playbook"
    assert r["knowledge"]["external_calls"] == 0

