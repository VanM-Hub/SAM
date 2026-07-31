"""Sprint 175 — Memory Runtime Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.memory.runtime.memory_runtime import MemoryRuntime, MemoryRunResult
from sam.memory.runtime.memory_pipeline import (
    MemoryPipeline, MemoryPipelineRun, MemoryPipelineStage,
)
from sam.memory.runtime.memory_engine import MemoryEngine, MemoryEngineInfo
from sam.memory.runtime.memory_summary import MemorySummary, MemorySummarizer
from sam.memory.runtime.memory_statistics import (
    MemoryStatistics, MemoryStatisticsCollector,
)
from sam.memory.runtime.conversation_runtime import ConversationRuntimeBridge
from sam.memory.runtime.dashboard_runtime import DashboardRuntimeBridge
from sam.memory.foundation.memory_registry import MemoryRegistry
from sam.memory.foundation.memory_descriptor import MemoryDescriptor
from sam.memory.foundation.memory_capability import MemoryCapability
from sam.memory.foundation.memory_contract import MemoryContract
from sam.memory.dashboard.memory_dashboard import ExecutionCard


def _registry():
    r = MemoryRegistry()
    r.register(MemoryDescriptor("mem1", "Short Term", category="short_term"))
    r.attach_capability(MemoryCapability("c1", "mem1", operations=["retain"]))
    r.attach_contract(MemoryContract("ct1", "mem1"))
    return r


class TestMemoryRuntime:
    def test_version(self):
        assert MemoryRuntime.RUNTIME_VERSION == "1.0.0"

    def test_pipeline_exists(self):
        rt = MemoryRuntime(_registry())
        res = rt.pipeline("mem1")
        assert res.ok is True
        assert res.external_calls == 0

    def test_pipeline_missing(self):
        rt = MemoryRuntime(MemoryRegistry())
        res = rt.pipeline("nope")
        assert res.ok is False

    def test_run(self):
        rt = MemoryRuntime(_registry())
        res = rt.run("mem1")
        assert res.ok is True

    def test_no_store(self):
        rt = MemoryRuntime(_registry())
        res = rt.run("mem1")
        assert "preview" in res.detail


class TestMemoryRunResult:
    def test_default(self):
        assert MemoryRunResult("m1").ok is False

    def test_immutable(self):
        res = MemoryRunResult("m1")
        with pytest.raises(FrozenInstanceError):
            res.ok = True


class TestMemoryPipeline:
    def test_run(self):
        p = MemoryPipeline(_registry())
        run = p.run("mem1")
        assert run.ok is True
        assert run.external_calls == 0
        assert len(run.stages) == 5

    def test_stage_order(self):
        p = MemoryPipeline(_registry())
        run = p.run("mem1")
        names = [s.name for s in run.stages]
        assert names == ["descriptor", "record", "builder", "snapshot", "preview"]

    def test_missing(self):
        p = MemoryPipeline(MemoryRegistry())
        run = p.run("nope")
        assert run.ok is False
        assert len(run.stages) == 1


class TestMemoryPipelineRun:
    def test_default(self):
        assert MemoryPipelineRun().ok is False

    def test_immutable(self):
        run = MemoryPipelineRun()
        with pytest.raises(FrozenInstanceError):
            run.ok = True


class TestMemoryPipelineStage:
    def test_immutable(self):
        s = MemoryPipelineStage("a")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestMemoryEngine:
    def test_info(self):
        e = MemoryEngine(MemoryRuntime(_registry())).info()
        assert e.preview_only is True
        assert e.deterministic is True

    def test_health(self):
        e = MemoryEngine(MemoryRuntime(_registry()))
        assert e.health() is True

    def test_run(self):
        e = MemoryEngine(MemoryRuntime(_registry()))
        assert e.run("mem1").ok is True


class TestMemoryEngineInfo:
    def test_default(self):
        assert MemoryEngineInfo("1.0").preview_only is True


class TestMemorySummary:
    def test_summary(self):
        s = MemorySummarizer(_registry()).summary()
        assert s.total_memories == 1
        assert s.by_category["short_term"] == 1
        assert s.external_calls == 0

    def test_immutable(self):
        s = MemorySummary()
        with pytest.raises(FrozenInstanceError):
            s.total_memories = 1


class TestMemoryStatistics:
    def test_collect(self):
        st = MemoryStatisticsCollector(_registry()).collect()
        assert st.total == 1
        assert st.with_capability == 1
        assert st.with_contract == 1
        assert st.external_calls == 0

    def test_immutable(self):
        st = MemoryStatistics()
        with pytest.raises(FrozenInstanceError):
            st.total = 1


class TestConversationRuntimeBridge:
    def test_summary(self):
        b = ConversationRuntimeBridge(MemoryRuntime(_registry()))
        assert b.summary()["total"] == 1
        assert b.summary()["external_calls"] == 0

    def test_run_status(self):
        b = ConversationRuntimeBridge(MemoryRuntime(_registry()))
        assert b.run_status("mem1")["ok"] is True


class TestDashboardRuntimeBridge:
    def test_five_cards(self):
        b = DashboardRuntimeBridge(MemoryRuntime(_registry()))
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardRuntimeBridge(MemoryRuntime(_registry()))
        assert b.overview_card().verdict == "ready"


class TestRuntimeImmutability:
    DTO_CLASSES = [
        MemoryRunResult, MemoryPipelineRun, MemoryPipelineStage,
        MemoryEngineInfo, MemorySummary, MemoryStatistics,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
