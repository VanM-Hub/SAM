"""Sprint 191 — Cognitive Runtime Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.cognitive_runtime.runtime.cognitive_runtime import (
    CognitiveRuntime, CognitiveRunResult,
)
from sam.cognitive_runtime.runtime.cognitive_pipeline import (
    CognitivePipeline, CognitivePipelineRun, CognitivePipelineStage,
)
from sam.cognitive_runtime.runtime.cognitive_engine import (
    CognitiveEngine, CognitiveEngineInfo,
)
from sam.cognitive_runtime.runtime.cognitive_summary import (
    CognitiveSummary, CognitiveSummarizer,
)
from sam.cognitive_runtime.runtime.cognitive_statistics import (
    CognitiveStatistics, CognitiveStatisticsItem, CognitiveStatisticsCollector,
)
from sam.cognitive_runtime.runtime.conversation_runtime import ConversationRuntimeBridge
from sam.cognitive_runtime.runtime.dashboard_runtime import DashboardRuntimeBridge
from sam.cognitive_runtime.foundation.cognitive_registry import CognitiveRegistry
from sam.cognitive_runtime.foundation.cognitive_descriptor import CognitiveDescriptor
from sam.cognitive_runtime.context.cognitive_context import CognitiveContext
from sam.cognitive_runtime.dashboard import ExecutionCard


def _registry():
    r = CognitiveRegistry()
    r.register(CognitiveDescriptor("cog1", "Core", category="core"))
    return r


class TestCognitiveRuntime:
    def test_run_ok(self):
        r = CognitiveRuntime(_registry()).run("cog1")
        assert r.ok is True
        assert r.cognitive_id == "cog1"
        assert r.external_calls == 0
        assert r.inferred is False

    def test_run_missing(self):
        r = CognitiveRuntime(CognitiveRegistry()).run("nope")
        assert r.ok is False
        assert r.external_calls == 0

    def test_engine_info(self):
        info = CognitiveRuntime(_registry()).engine_info()
        assert info["no_inference"] is True
        assert info["preview_only"] is True


class TestCognitiveRunResult:
    def test_default(self):
        assert CognitiveRunResult().external_calls == 0

    def test_immutable(self):
        r = CognitiveRunResult()
        with pytest.raises(FrozenInstanceError):
            r.ok = False


class TestCognitivePipeline:
    def test_stages(self):
        p = CognitivePipeline(_registry())
        assert p.stages() == ["descriptor", "context", "snapshot", "workspace", "preview"]

    def test_run_ok(self):
        p = CognitivePipeline(_registry()).run("cog1")
        assert p.ok is True
        assert len(p.stages) == 5
        assert p.external_calls == 0

    def test_run_missing(self):
        p = CognitivePipeline(CognitiveRegistry()).run("nope")
        assert p.ok is False
        assert len(p.stages) == 1


class TestCognitivePipelineRun:
    def test_default(self):
        assert CognitivePipelineRun().ok is False

    def test_immutable(self):
        p = CognitivePipelineRun()
        with pytest.raises(FrozenInstanceError):
            p.ok = True


class TestCognitivePipelineStage:
    def test_immutable(self):
        s = CognitivePipelineStage("x")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestCognitiveEngine:
    def test_info(self):
        info = CognitiveEngine().info()
        assert info.no_inference is True
        assert info.is_llm is False
        assert info.is_ai is False
        assert info.deterministic is True


class TestCognitiveEngineInfo:
    def test_immutable(self):
        i = CognitiveEngineInfo()
        with pytest.raises(FrozenInstanceError):
            i.no_inference = False


class TestCognitiveSummarizer:
    def test_summarize(self):
        ctx = CognitiveContext(cognitive_id="c1", entries=["a"], scope="knowledge")
        s = CognitiveSummarizer().summarize(ctx)
        assert s.cognitive_id == "c1"
        assert s.entry_count == 1
        assert s.scope == "knowledge"


class TestCognitiveSummary:
    def test_immutable(self):
        s = CognitiveSummary()
        with pytest.raises(FrozenInstanceError):
            s.entry_count = 1


class TestCognitiveStatisticsCollector:
    def test_collect(self):
        s = CognitiveStatisticsCollector(_registry()).collect()
        assert s.total == 1
        assert s.registered == 1


class TestCognitiveStatistics:
    def test_default(self):
        assert CognitiveStatistics().total == 0

    def test_immutable(self):
        s = CognitiveStatistics()
        with pytest.raises(FrozenInstanceError):
            s.total = 1


class TestCognitiveStatisticsItem:
    def test_default(self):
        assert CognitiveStatisticsItem().registered is False


class TestConversationRuntimeBridge:
    def test_5_queries(self):
        b = ConversationRuntimeBridge(_registry())
        assert b.query_1_run("cog1")["ok"] is True
        assert b.query_2_pipeline("cog1")["ok"] is True
        assert len(b.query_3_stages()) == 5
        assert b.query_4_statistics()["total"] == 1
        assert b.query_5_engine()["is_llm"] is False


class TestDashboardRuntimeBridge:
    def test_five_cards(self):
        b = DashboardRuntimeBridge(_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardRuntimeBridge(_registry())
        assert b.overview_card().verdict == "ready"


class TestRuntimeImmutability:
    DTO_CLASSES = [
        CognitiveRunResult, CognitivePipelineRun, CognitivePipelineStage,
        CognitiveEngineInfo, CognitiveSummary, CognitiveStatistics,
        CognitiveStatisticsItem,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
