"""Knowledge Runtime — Capability & Pipeline Suite (Dedicated).

WP-04 EA-004 / Program B — suite DEDICATED capability Knowledge Runtime.
Memverifikasi capability preview-only (tanpa inference, tanpa external call)
dan jalur pipeline integrasi (Sprint 187).

Read-only, deterministik.
"""
from sam.knowledge_runtime.foundation.knowledge_descriptor import KnowledgeDescriptor
from sam.knowledge_runtime.foundation.knowledge_registry import KnowledgeRegistry
from sam.knowledge_runtime.runtime.knowledge_runtime import KnowledgeRuntime
from sam.knowledge_runtime.integration.knowledge_runtime_pipeline import (
    KnowledgeRuntimePipeline,
    KnowledgeIntegrationStage,
    INTEGRATION_ROUTE,
)


def _reg():
    r = KnowledgeRegistry()
    r.register(KnowledgeDescriptor("kn1", "Pipeline Knowledge", category="domain"))
    return r


class TestPreviewOnlyCapability:
    """Knowledge Runtime adalah preview-only: tidak ada external call / inference."""

    def test_preview_default(self):
        """Capability default harus preview=True (tanpa promotion)."""
        from sam.knowledge_runtime.foundation.knowledge_capability import KnowledgeCapability
        assert KnowledgeCapability("c1", "kn1").preview_only is True

    def test_runtime_never_calls_external(self):
        rt = KnowledgeRuntime(_reg())
        res = rt.run("kn1")
        assert res.ok is True
        assert res.external_calls == 0

    def test_summary_external_zero(self):
        from sam.knowledge_runtime.runtime.knowledge_summary import KnowledgeSummarizer
        assert KnowledgeSummarizer(_reg()).summary().external_calls == 0


class TestIntegrationPipeline:
    """Pipeline integrasi (Sprint 187) — jalur end-to-end Knowledge Runtime."""

    def test_route_order(self):
        p = KnowledgeRuntimePipeline(_reg())
        assert p.route() == INTEGRATION_ROUTE
        assert "knowledge" in p.route()

    def test_pipeline_ok_when_registered(self):
        p = KnowledgeRuntimePipeline(_reg())
        run = p.run("kn1")
        assert run.ok is True
        assert run.knowledge_id == "kn1"
        assert run.external_calls == 0
        # semua stage hadir
        names = [s.name for s in run.stages]
        assert "knowledge" in names
        assert "execution_preview" in names
        assert all(s.ok for s in run.stages)

    def test_pipeline_fail_when_missing(self):
        p = KnowledgeRuntimePipeline(KnowledgeRegistry())
        run = p.run("ghost")
        assert run.ok is False
        # stage knowledge menandai not found
        ks = [s for s in run.stages if s.name == "knowledge"][0]
        assert ks.ok is False
        assert ks.detail == "not found"

    def test_pipeline_stage_immutable(self):
        s = KnowledgeIntegrationStage("knowledge", True, "found")
        assert s.ok is True
        try:
            s.ok = False
            assert False, "stage harus immutable"
        except Exception:
            pass
