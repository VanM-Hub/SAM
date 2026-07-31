"""Sprint 223 — Artifact Runtime Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.artifact_runtime.runtime.artifact_runtime import (
    ArtifactRuntime, ArtifactRunResult,
)
from sam.artifact_runtime.runtime.artifact_pipeline import (
    ArtifactPipeline, ArtifactPipelineRun, ArtifactPipelineStage,
)
from sam.artifact_runtime.runtime.artifact_engine import (
    ArtifactEngine, ArtifactEngineInfo,
)
from sam.artifact_runtime.runtime.artifact_summary import (
    ArtifactSummary, ArtifactSummarizer,
)
from sam.artifact_runtime.runtime.artifact_statistics import (
    ArtifactStatistics, ArtifactCollector,
)
from sam.artifact_runtime.runtime.conversation_runtime import (
    ConversationRuntimeBridge,
)
from sam.artifact_runtime.runtime.dashboard_runtime import DashboardRuntimeBridge
from sam.artifact_runtime.dashboard import PolicyCard


class TestArtifactRuntime:
    def test_run_ok(self):
        res = ArtifactRuntime().run("out", "report")
        assert res.ok is True
        assert res.external_calls == 0
        assert res.preview.stored is False
        assert res.preview.published is False

    def test_run_empty(self):
        res = ArtifactRuntime().run("")
        assert res.ok is False
        assert res.external_calls == 0


class TestArtifactRunResult:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactRunResult().ok = True


class TestArtifactPipeline:
    def test_route(self):
        p = ArtifactPipeline(ArtifactRuntime())
        assert p.route() == ("descriptor", "artifact", "builder", "preview")

    def test_run(self):
        run = ArtifactPipeline(ArtifactRuntime()).run("out")
        assert run.ok is True
        assert run.external_calls == 0
        assert len(run.stages) == 4


class TestArtifactPipelineRun:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactPipelineRun().ok = False


class TestArtifactPipelineStage:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactPipelineStage("x").ok = False


class TestArtifactEngine:
    def test_not_ai(self):
        info = ArtifactEngine().describe()
        assert info.is_llm is False
        assert info.is_ai is False
        assert info.preview_only is True


class TestArtifactEngineInfo:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactEngineInfo().is_ai = True


class TestArtifactSummarizer:
    def test_summarize(self):
        s = ArtifactSummarizer().summarize(("a", "b"), ("report", "report"))
        assert s.total == 2
        assert s.no_storage is True
        assert s.preview_only is True


class TestArtifactSummary:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactSummary().total = 5


class TestArtifactCollector:
    def test_collect(self):
        s = ArtifactCollector().collect(("report", "log", "report"))
        assert s.total == 3
        assert dict(s.by_kind)["report"] == 2
        assert s.external_calls == 0


class TestArtifactStatistics:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactStatistics().total = 1


class TestConversationRuntimeBridge:
    def test_five_queries(self):
        b = ConversationRuntimeBridge()
        assert b.query_1_run("ok")["ok"] is True
        assert b.query_2_route() == ("descriptor", "artifact", "builder", "preview")
        assert b.query_3_engine()["is_llm"] is False
        assert b.query_4_summary()["total"] == 2
        assert b.query_5_statistics()["external_calls"] == 0


class TestDashboardRuntimeBridge:
    def test_five_cards(self):
        cards = DashboardRuntimeBridge().cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)


class TestRuntimeImmutability:
    DTO = [ArtifactRunResult, ArtifactPipelineRun, ArtifactPipelineStage,
           ArtifactEngineInfo, ArtifactSummary, ArtifactStatistics]

    def test_all_frozen(self):
        for cls in self.DTO:
            assert cls.__dataclass_params__.frozen
