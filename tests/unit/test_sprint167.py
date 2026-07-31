"""Sprint 167 — Skill Runtime Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.skills.runtime.skill_runtime import SkillRuntime, SkillRunResult
from sam.skills.runtime.skill_pipeline import SkillPipeline, SkillPipelineRun, SkillPipelineStage
from sam.skills.runtime.skill_engine import SkillEngine, SkillEngineInfo
from sam.skills.runtime.skill_summary import SkillSummary, SkillSummarizer
from sam.skills.runtime.skill_statistics import SkillStatistics, SkillStatisticsCollector
from sam.skills.runtime.conversation_runtime import ConversationRuntimeBridge
from sam.skills.runtime.dashboard_runtime import DashboardRuntimeBridge
from sam.skills.foundation.skill_registry import SkillRegistry
from sam.skills.foundation.skill_descriptor import SkillDescriptor
from sam.skills.foundation.skill_capability import SkillCapability
from sam.skills.foundation.skill_contract import SkillContract
from sam.skills.dashboard.skill_dashboard import ExecutionCard


def _registry():
    r = SkillRegistry()
    r.register(SkillDescriptor("skill1", "Read", category="io"))
    r.attach_capability(SkillCapability("c1", "skill1", operations=["read"]))
    r.attach_contract(SkillContract("ct1", "skill1"))
    return r


class TestSkillRuntime:
    def test_version(self):
        assert SkillRuntime.RUNTIME_VERSION == "1.0.0"

    def test_pipeline_exists(self):
        rt = SkillRuntime(_registry())
        res = rt.pipeline("skill1")
        assert res.ok is True
        assert res.external_calls == 0

    def test_pipeline_missing(self):
        rt = SkillRuntime(SkillRegistry())
        res = rt.pipeline("nope")
        assert res.ok is False

    def test_run(self):
        rt = SkillRuntime(_registry())
        res = rt.run("skill1")
        assert res.ok is True

    def test_external_always_zero(self):
        rt = SkillRuntime(_registry())
        rt.run("skill1")
        assert rt.pipeline("skill1").external_calls == 0


class TestSkillRunResult:
    def test_default(self):
        assert SkillRunResult("s1").ok is False

    def test_immutable(self):
        res = SkillRunResult("s1")
        with pytest.raises(FrozenInstanceError):
            res.ok = True


class TestSkillPipeline:
    def test_run(self):
        p = SkillPipeline(_registry())
        run = p.run("skill1")
        assert run.ok is True
        assert run.external_calls == 0
        assert len(run.stages) == 5

    def test_stage_order(self):
        p = SkillPipeline(_registry())
        run = p.run("skill1")
        names = [s.name for s in run.stages]
        assert names == ["descriptor", "definition", "builder", "workflow", "preview"]

    def test_missing(self):
        p = SkillPipeline(SkillRegistry())
        run = p.run("nope")
        assert run.ok is False
        assert len(run.stages) == 1


class TestSkillPipelineRun:
    def test_default(self):
        assert SkillPipelineRun().ok is False

    def test_immutable(self):
        run = SkillPipelineRun()
        with pytest.raises(FrozenInstanceError):
            run.ok = True


class TestSkillPipelineStage:
    def test_immutable(self):
        s = SkillPipelineStage("a")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestSkillEngine:
    def test_info(self):
        e = SkillEngine(SkillRuntime(_registry())).info()
        assert e.preview_only is True
        assert e.deterministic is True

    def test_health(self):
        e = SkillEngine(SkillRuntime(_registry()))
        assert e.health() is True

    def test_run(self):
        e = SkillEngine(SkillRuntime(_registry()))
        assert e.run("skill1").ok is True


class TestSkillEngineInfo:
    def test_default(self):
        assert SkillEngineInfo("1.0").preview_only is True


class TestSkillSummary:
    def test_summary(self):
        s = SkillSummarizer(_registry()).summary()
        assert s.total_skills == 1
        assert s.by_category["io"] == 1
        assert s.external_calls == 0

    def test_immutable(self):
        s = SkillSummary()
        with pytest.raises(FrozenInstanceError):
            s.total_skills = 1


class TestSkillStatistics:
    def test_collect(self):
        st = SkillStatisticsCollector(_registry()).collect()
        assert st.total == 1
        assert st.with_capability == 1
        assert st.with_contract == 1
        assert st.external_calls == 0

    def test_immutable(self):
        st = SkillStatistics()
        with pytest.raises(FrozenInstanceError):
            st.total = 1


class TestConversationRuntimeBridge:
    def test_summary(self):
        b = ConversationRuntimeBridge(SkillRuntime(_registry()))
        assert b.summary()["total"] == 1
        assert b.summary()["external_calls"] == 0

    def test_run_status(self):
        b = ConversationRuntimeBridge(SkillRuntime(_registry()))
        assert b.run_status("skill1")["ok"] is True


class TestDashboardRuntimeBridge:
    def test_five_cards(self):
        b = DashboardRuntimeBridge(SkillRuntime(_registry()))
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardRuntimeBridge(SkillRuntime(_registry()))
        assert b.overview_card().verdict == "ready"


class TestRuntimeImmutability:
    DTO_CLASSES = [
        SkillRunResult, SkillPipelineRun, SkillPipelineStage,
        SkillEngineInfo, SkillSummary, SkillStatistics,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
