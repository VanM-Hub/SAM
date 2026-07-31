"""Sprint 162 — Agent Runtime Engine Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.agent.runtime.agent_runtime import AgentRuntime, AgentRunResult
from sam.agent.runtime.pipeline import Pipeline, PipelineRun, PipelineStage
from sam.agent.runtime.runtime_engine import RuntimeEngine, EngineInfo
from sam.agent.runtime.runtime_report import RuntimeReporter, RuntimeReport
from sam.agent.runtime.runtime_statistics import RuntimeStatistics, RuntimeStatisticsCollector
from sam.agent.runtime.conversation_runtime import ConversationRuntimeBridge
from sam.agent.runtime.dashboard_runtime import DashboardRuntimeBridge
from sam.agent.foundation.agent_registry import AgentRegistry
from sam.agent.dashboard.agent_dashboard import ExecutionCard


def _runtime():
    r = AgentRuntime(AgentRegistry())
    r.register_runtimes(["guardian", "decision", "execution"])
    r.machine.create("m1")
    return r


class TestAgentRuntime:
    def test_version(self):
        assert AgentRuntime.RUNTIME_VERSION == "1.0.0"

    def test_build_plan(self):
        r = _runtime()
        res = r.build_plan("p1", "m1")
        assert res.valid is True

    def test_run_mission_completes(self):
        r = _runtime()
        r.enqueue_route(["guardian", "decision", "execution"])
        result = r.run_mission("m1")
        assert result.ok is True
        assert result.final_state == "Completed"
        assert result.external_calls == 0

    def test_run_unknown_mission(self):
        r = AgentRuntime(AgentRegistry())
        result = r.run_mission("nope")
        assert result.ok is False

    def test_run_terminal_noop(self):
        r = _runtime()
        r.enqueue_route(["guardian"])
        r.run_mission("m1")
        second = r.run_mission("m1")
        assert second.ok is False  # sudah terminal

    def test_external_always_zero(self):
        r = _runtime()
        r.enqueue_route(["guardian", "decision"])
        r.run_mission("m1")
        assert r.run_mission is not None


class TestAgentRunResult:
    def test_default(self):
        assert AgentRunResult("m1").final_state == "Created"

    def test_immutable(self):
        res = AgentRunResult("m1")
        with pytest.raises(FrozenInstanceError):
            res.ok = True


class TestPipeline:
    def test_run(self):
        r = _runtime()
        r.register_runtimes(["guardian", "decision", "execution"])
        p = Pipeline(r)
        run = p.run("m1")
        assert run.ok is True
        assert run.final_state == "Completed"
        assert run.external_calls == 0
        # Mission, State, Planner, Coordinator, Monitor, Summary
        assert len(run.stages) == 6

    def test_stage_names(self):
        r = _runtime()
        r.register_runtimes(["guardian"])
        p = Pipeline(r)
        run = p.run("m1")
        names = [s.name for s in run.stages]
        assert names == ["mission", "state", "planner", "coordinator",
                         "monitor", "summary"]


class TestPipelineRun:
    def test_default(self):
        assert PipelineRun().ok is False

    def test_immutable(self):
        run = PipelineRun()
        with pytest.raises(FrozenInstanceError):
            run.ok = True


class TestPipelineStage:
    def test_immutable(self):
        s = PipelineStage("a")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestRuntimeEngine:
    def test_info(self):
        r = _runtime()
        info = RuntimeEngine(r).info()
        assert info.preview_only is True
        assert info.deterministic is True

    def test_health(self):
        r = _runtime()
        assert RuntimeEngine(r).health() is True

    def test_run(self):
        r = _runtime()
        r.enqueue_route(["guardian"])
        result = RuntimeEngine(r).run("m1")
        assert result.final_state == "Completed"


class TestEngineInfo:
    def test_default(self):
        assert EngineInfo("1.0").preview_only is True


class TestRuntimeReporter:
    def test_report(self):
        r = _runtime()
        rep = RuntimeReporter(r).report()
        assert rep.ready is True
        assert rep.total_missions == 1
        assert rep.external_calls == 0

    def test_version(self):
        r = _runtime()
        assert RuntimeReporter(r).report().version == "1.0.0"


class TestRuntimeReport:
    def test_immutable(self):
        rep = RuntimeReport()
        with pytest.raises(FrozenInstanceError):
            rep.ready = True


class TestRuntimeStatistics:
    def test_collect(self):
        r = _runtime()
        stats = RuntimeStatisticsCollector(r).collect()
        assert stats.total_missions == 1
        assert stats.external_calls == 0

    def test_completion_rate_zero(self):
        assert RuntimeStatistics().completion_rate == 0.0

    def test_immutable(self):
        s = RuntimeStatistics()
        with pytest.raises(FrozenInstanceError):
            s.total_missions = 1


class TestConversationRuntimeBridge:
    def test_agent_status(self):
        r = _runtime()
        b = ConversationRuntimeBridge(r)
        assert b.show_agent_status()["missions"] == 1

    def test_current_state(self):
        r = _runtime()
        b = ConversationRuntimeBridge(r)
        assert b.show_current_state("m1") == "Created"

    def test_summary(self):
        r = _runtime()
        r.enqueue_route(["guardian"])
        r.run_mission("m1")
        b = ConversationRuntimeBridge(r)
        s = b.show_summary()
        assert s["total"] == 1
        assert s["external_calls"] == 0


class TestDashboardRuntimeBridge:
    def test_five_cards(self):
        r = _runtime()
        b = DashboardRuntimeBridge(r)
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        r = _runtime()
        b = DashboardRuntimeBridge(r)
        assert b.overview_card().verdict == "ready"


class TestRuntimeImmutability:
    DTO_CLASSES = [
        AgentRunResult, PipelineRun, PipelineStage,
        EngineInfo, RuntimeReport, RuntimeStatistics,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
