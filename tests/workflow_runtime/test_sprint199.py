"""Sprint 199 — Workflow Runtime Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.workflow_runtime.runtime.workflow_runtime import (
    WorkflowRuntime, WorkflowRunResult,
)
from sam.workflow_runtime.runtime.workflow_pipeline import (
    WorkflowPipeline, WorkflowPipelineRun, WorkflowPipelineStage,
)
from sam.workflow_runtime.runtime.workflow_engine import (
    WorkflowEngine, WorkflowEngineInfo,
)
from sam.workflow_runtime.runtime.workflow_summary import (
    WorkflowSummary, WorkflowSummarizer,
)
from sam.workflow_runtime.runtime.workflow_statistics import (
    WorkflowStatistics, WorkflowStatisticsItem, WorkflowStatisticsCollector,
)
from sam.workflow_runtime.runtime.conversation_runtime import ConversationRuntimeBridge
from sam.workflow_runtime.runtime.dashboard_runtime import DashboardRuntimeBridge
from sam.workflow_runtime.foundation.workflow_registry import WorkflowRegistry
from sam.workflow_runtime.foundation.workflow_descriptor import WorkflowDescriptor
from sam.workflow_runtime.model.workflow import Workflow
from sam.workflow_runtime.dashboard import WorkflowCard


def _registry():
    r = WorkflowRegistry()
    r.register(WorkflowDescriptor("wf1", "Onboard", category="process"))
    return r


class TestWorkflowRuntime:
    def test_run_ok(self):
        r = WorkflowRuntime(_registry()).run("wf1")
        assert r.ok is True
        assert r.workflow_id == "wf1"
        assert r.external_calls == 0
        assert r.scheduled is False

    def test_run_missing(self):
        r = WorkflowRuntime(WorkflowRegistry()).run("nope")
        assert r.ok is False
        assert r.external_calls == 0

    def test_engine_info(self):
        info = WorkflowRuntime(_registry()).engine_info()
        assert info["no_inference"] is True
        assert info["preview_only"] is True


class TestWorkflowRunResult:
    def test_default(self):
        assert WorkflowRunResult().external_calls == 0

    def test_immutable(self):
        r = WorkflowRunResult()
        with pytest.raises(FrozenInstanceError):
            r.ok = False


class TestWorkflowPipeline:
    def test_stages(self):
        p = WorkflowPipeline(_registry())
        assert p.stages() == ["descriptor", "workflow", "builder", "preview"]

    def test_run_ok(self):
        p = WorkflowPipeline(_registry()).run("wf1")
        assert p.ok is True
        assert len(p.stages) == 4
        assert p.external_calls == 0

    def test_run_missing(self):
        p = WorkflowPipeline(WorkflowRegistry()).run("nope")
        assert p.ok is False
        assert len(p.stages) == 1


class TestWorkflowPipelineRun:
    def test_default(self):
        assert WorkflowPipelineRun().ok is False

    def test_immutable(self):
        p = WorkflowPipelineRun()
        with pytest.raises(FrozenInstanceError):
            p.ok = True


class TestWorkflowPipelineStage:
    def test_immutable(self):
        s = WorkflowPipelineStage("x")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestWorkflowEngine:
    def test_info(self):
        info = WorkflowEngine().info()
        assert info.no_inference is True
        assert info.is_llm is False
        assert info.is_ai is False
        assert info.deterministic is True


class TestWorkflowEngineInfo:
    def test_immutable(self):
        i = WorkflowEngineInfo()
        with pytest.raises(FrozenInstanceError):
            i.no_inference = False


class TestWorkflowSummarizer:
    def test_summarize(self):
        wf = Workflow("w1", steps=["s1"], scope="process")
        s = WorkflowSummarizer().summarize(wf)
        assert s.workflow_id == "w1"
        assert s.step_count == 1
        assert s.scope == "process"


class TestWorkflowSummary:
    def test_immutable(self):
        s = WorkflowSummary()
        with pytest.raises(FrozenInstanceError):
            s.step_count = 1


class TestWorkflowStatisticsCollector:
    def test_collect(self):
        s = WorkflowStatisticsCollector(_registry()).collect()
        assert s.total == 1
        assert s.registered == 1


class TestWorkflowStatistics:
    def test_default(self):
        assert WorkflowStatistics().total == 0

    def test_immutable(self):
        s = WorkflowStatistics()
        with pytest.raises(FrozenInstanceError):
            s.total = 1


class TestWorkflowStatisticsItem:
    def test_default(self):
        assert WorkflowStatisticsItem().registered is False


class TestConversationRuntimeBridge:
    def test_5_queries(self):
        b = ConversationRuntimeBridge(_registry())
        assert b.query_1_run("wf1")["ok"] is True
        assert b.query_2_pipeline("wf1")["ok"] is True
        assert len(b.query_3_stages()) == 4
        assert b.query_4_statistics()["total"] == 1
        assert b.query_5_engine()["is_llm"] is False


class TestDashboardRuntimeBridge:
    def test_five_cards(self):
        b = DashboardRuntimeBridge(_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, WorkflowCard) for c in cards)

    def test_overview(self):
        b = DashboardRuntimeBridge(_registry())
        assert b.overview_card().verdict == "ready"


class TestRuntimeImmutability:
    DTO_CLASSES = [
        WorkflowRunResult, WorkflowPipelineRun, WorkflowPipelineStage,
        WorkflowEngineInfo, WorkflowSummary, WorkflowStatistics,
        WorkflowStatisticsItem,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
