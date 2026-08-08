"""Memory Runtime — Capability & Operational Path Suite (Evidence, WP-B1).

Program B / EA-004 — suite DEDICATED capability Memory Runtime + jalur
operational AD-ENG-002 (Conversation -> RuntimeService -> ExecutionEngine ->
MemoryPreviewConsumer -> MemoryRegistry -> ConversationMemoryBridge -> STOP).

Memverifikasi Memory sebagai capability MANDIRI, preview-only (tanpa
storage/retrieval/inference), dan membuktikan jalur operational yang SUDAH ADA
berfungsi lewat API publik — tanpa mengubah source.

Read-only, deterministik.
"""
from sam.memory.foundation.memory_descriptor import MemoryDescriptor
from sam.memory.foundation.memory_registry import MemoryRegistry
from sam.memory.runtime.memory_runtime import MemoryRuntime
from sam.memory.integration.memory_runtime_pipeline import (
    MemoryRuntimePipeline,
    INTEGRATION_ROUTE,
)
from sam.runtime_service.api import MemoryPreviewConsumer, MemoryContextPreview


def _reg():
    r = MemoryRegistry()
    r.register(MemoryDescriptor("mem1", "Operational Memory", category="session"))
    return r


class TestPreviewOnlyCapability:
    """Memory Runtime adalah preview-only: tanpa external call / storage / inference."""

    def test_preview_default(self):
        from sam.memory.foundation.memory_capability import MemoryCapability
        assert MemoryCapability("c1", "mem1").preview_only is True

    def test_runtime_never_calls_external(self):
        assert MemoryRuntime(_reg()).run("mem1").external_calls == 0

    def test_summary_external_zero(self):
        from sam.memory.runtime.memory_summary import MemorySummarizer
        assert MemorySummarizer(_reg()).summary().external_calls == 0

    def test_preview_no_storage_retrieval_executed(self):
        """Resolve operational tidak boleh memunculkan storage/retrieval/execution."""
        consumer = MemoryPreviewConsumer(registry=_reg())
        mp = consumer.resolve_memory("mem1")
        assert mp.found is True
        assert mp.external_calls == 0
        d = mp.as_dict()
        for banned in ("executed", "retrieved", "stored"):
            assert banned not in d, f"preview memunculkan {banned}"


class TestOperationalPath(TestPreviewOnlyCapability):
    """Jalur operational AD-ENG-002 yang SUDAH ADA — dibuktikan via API publik."""

    def test_consumer_is_capability(self):
        """Memory = capability mandiri (punya consumer sendiri di runtime_service)."""
        consumer = MemoryPreviewConsumer(registry=_reg())
        assert "mem1" in consumer.list_memories()

    def test_resolve_found(self):
        consumer = MemoryPreviewConsumer(registry=_reg())
        mp = consumer.resolve_memory("mem1")
        assert isinstance(mp, MemoryContextPreview)
        assert mp.found is True
        assert mp.name == "Operational Memory"
        assert mp.integration_ok is True

    def test_resolve_unknown(self):
        consumer = MemoryPreviewConsumer(registry=_reg())
        mp = consumer.resolve_memory("ghost")
        assert mp.found is False
        assert mp.external_calls == 0

    def test_full_conversation_preview_path(self):
        """Conversation -> RuntimeService -> ExecutionEngine(preview) -> Memory."""
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
        mc = MemoryPreviewConsumer(registry=_reg())
        ctx = ConversationExecutionContext(conversation_id="w1", request="ingat konteks")
        r = gw.preview_with_memory(ctx, mc, "mem1", "exec-1")
        assert r["execution"]["executed"] is False
        assert r["execution"]["external_calls"] == 0
        assert r["memory"]["found"] is True
        assert r["memory"]["name"] == "Operational Memory"
        assert r["memory"]["external_calls"] == 0


class TestIntegrationPipeline:
    """Pipeline integrasi Memory (Sprint 179) — jalur end-to-end."""

    def test_route_order(self):
        p = MemoryRuntimePipeline(_reg())
        assert p.route() == INTEGRATION_ROUTE
        assert "memory" in p.route()

    def test_pipeline_ok_when_registered(self):
        run = MemoryRuntimePipeline(_reg()).run("mem1")
        assert run.ok is True
        assert run.memory_id == "mem1"
        assert run.external_calls == 0
        names = [s.name for s in run.stages]
        assert "memory" in names
        assert "execution_preview" in names
        assert all(s.ok for s in run.stages)

    def test_pipeline_fail_when_missing(self):
        run = MemoryRuntimePipeline(MemoryRegistry()).run("ghost")
        assert run.ok is False
        ms = [s for s in run.stages if s.name == "memory"][0]
        assert ms.ok is False
        assert ms.detail == "not found"
