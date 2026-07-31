"""Sprint 183 — Knowledge Runtime Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.knowledge_runtime.runtime.knowledge_runtime import (
    KnowledgeRuntime, KnowledgeRunResult,
)
from sam.knowledge_runtime.runtime.knowledge_pipeline import (
    KnowledgePipeline, KnowledgePipelineRun, KnowledgePipelineStage,
)
from sam.knowledge_runtime.runtime.knowledge_engine import (
    KnowledgeEngine, KnowledgeEngineInfo,
)
from sam.knowledge_runtime.runtime.knowledge_summary import (
    KnowledgeSummary, KnowledgeSummarizer,
)
from sam.knowledge_runtime.runtime.knowledge_statistics import (
    KnowledgeStatistics, KnowledgeStatisticsCollector,
)
from sam.knowledge_runtime.runtime.conversation_runtime import ConversationRuntimeBridge
from sam.knowledge_runtime.runtime.dashboard_runtime import DashboardRuntimeBridge
from sam.knowledge_runtime.foundation.knowledge_registry import KnowledgeRegistry
from sam.knowledge_runtime.foundation.knowledge_descriptor import KnowledgeDescriptor
from sam.knowledge_runtime.foundation.knowledge_capability import KnowledgeCapability
from sam.knowledge_runtime.foundation.knowledge_contract import KnowledgeContract
from sam.knowledge_runtime.dashboard.knowledge_dashboard import ExecutionCard


def _registry():
    r = KnowledgeRegistry()
    r.register(KnowledgeDescriptor("kn1", "Domain", category="domain"))
    r.attach_capability(KnowledgeCapability("c1", "kn1", operations=["fact"]))
    r.attach_contract(KnowledgeContract("ct1", "kn1"))
    return r


class TestKnowledgeRuntime:
    def test_version(self):
        assert KnowledgeRuntime.RUNTIME_VERSION == "1.0.0"

    def test_pipeline_exists(self):
        rt = KnowledgeRuntime(_registry())
        res = rt.pipeline("kn1")
        assert res.ok is True
        assert res.external_calls == 0

    def test_pipeline_missing(self):
        rt = KnowledgeRuntime(KnowledgeRegistry())
        res = rt.pipeline("nope")
        assert res.ok is False

    def test_run(self):
        rt = KnowledgeRuntime(_registry())
        res = rt.run("kn1")
        assert res.ok is True

    def test_no_inference(self):
        rt = KnowledgeRuntime(_registry())
        assert "no inference" in rt.run("kn1").detail


class TestKnowledgeRunResult:
    def test_default(self):
        assert KnowledgeRunResult("k1").ok is False

    def test_immutable(self):
        res = KnowledgeRunResult("k1")
        with pytest.raises(FrozenInstanceError):
            res.ok = True


class TestKnowledgePipeline:
    def test_run(self):
        p = KnowledgePipeline(_registry())
        run = p.run("kn1")
        assert run.ok is True
        assert run.external_calls == 0
        assert len(run.stages) == 5

    def test_stage_order(self):
        p = KnowledgePipeline(_registry())
        run = p.run("kn1")
        names = [s.name for s in run.stages]
        assert names == ["descriptor", "fact", "relation", "knowledge", "preview"]

    def test_missing(self):
        p = KnowledgePipeline(KnowledgeRegistry())
        run = p.run("nope")
        assert run.ok is False
        assert len(run.stages) == 1


class TestKnowledgePipelineRun:
    def test_default(self):
        assert KnowledgePipelineRun().ok is False

    def test_immutable(self):
        run = KnowledgePipelineRun()
        with pytest.raises(FrozenInstanceError):
            run.ok = True


class TestKnowledgePipelineStage:
    def test_immutable(self):
        s = KnowledgePipelineStage("a")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestKnowledgeEngine:
    def test_info(self):
        e = KnowledgeEngine(KnowledgeRuntime(_registry())).info()
        assert e.preview_only is True
        assert e.deterministic is True
        assert e.inference is False

    def test_health(self):
        e = KnowledgeEngine(KnowledgeRuntime(_registry()))
        assert e.health() is True

    def test_run(self):
        e = KnowledgeEngine(KnowledgeRuntime(_registry()))
        assert e.run("kn1").ok is True


class TestKnowledgeEngineInfo:
    def test_default(self):
        assert KnowledgeEngineInfo("1.0").inference is False


class TestKnowledgeSummary:
    def test_summary(self):
        s = KnowledgeSummarizer(_registry()).summary()
        assert s.total_knowledge == 1
        assert s.by_category["domain"] == 1
        assert s.external_calls == 0

    def test_immutable(self):
        s = KnowledgeSummary()
        with pytest.raises(FrozenInstanceError):
            s.total_knowledge = 1


class TestKnowledgeStatistics:
    def test_collect(self):
        st = KnowledgeStatisticsCollector(_registry()).collect()
        assert st.total == 1
        assert st.with_capability == 1
        assert st.with_contract == 1
        assert st.external_calls == 0

    def test_immutable(self):
        st = KnowledgeStatistics()
        with pytest.raises(FrozenInstanceError):
            st.total = 1


class TestConversationRuntimeBridge:
    def test_summary(self):
        b = ConversationRuntimeBridge(KnowledgeRuntime(_registry()))
        assert b.summary()["total"] == 1
        assert b.summary()["external_calls"] == 0

    def test_run_status(self):
        b = ConversationRuntimeBridge(KnowledgeRuntime(_registry()))
        assert b.run_status("kn1")["ok"] is True


class TestDashboardRuntimeBridge:
    def test_five_cards(self):
        b = DashboardRuntimeBridge(KnowledgeRuntime(_registry()))
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardRuntimeBridge(KnowledgeRuntime(_registry()))
        assert b.overview_card().verdict == "ready"


class TestRuntimeImmutability:
    DTO_CLASSES = [
        KnowledgeRunResult, KnowledgePipelineRun, KnowledgePipelineStage,
        KnowledgeEngineInfo, KnowledgeSummary, KnowledgeStatistics,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
