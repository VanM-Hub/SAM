"""Sprint 227 — Artifact Integration Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.artifact_runtime.integration.artifact_runtime_pipeline import (
    ArtifactRuntimePipeline, ArtifactRuntimePipelineRun, ArtifactIntegrationStage,
    INTEGRATION_ROUTE,
)
from sam.artifact_runtime.integration.artifact_runtime_registry import (
    ArtifactRuntimeRegistry, ArtifactRuntimeRegistryEntry,
)
from sam.artifact_runtime.integration.artifact_runtime_manifest import (
    ArtifactRuntimeManifest,
)
from sam.artifact_runtime.integration.artifact_runtime_report import (
    ArtifactRuntimeReport, ArtifactRuntimeReporter,
)
from sam.artifact_runtime.integration.artifact_runtime_summary import (
    ArtifactRuntimeSummary, ArtifactRuntimeSummarizer,
)
from sam.artifact_runtime.integration.conversation_integration import (
    ConversationIntegrationBridge,
)
from sam.artifact_runtime.integration.dashboard_integration import (
    DashboardIntegrationBridge,
)
from sam.artifact_runtime.foundation.artifact_registry import ArtifactRegistry
from sam.artifact_runtime.foundation.artifact_descriptor import ArtifactDescriptor
from sam.artifact_runtime.dashboard import PolicyCard


def _registry():
    r = ArtifactRegistry()
    r = r.register(ArtifactDescriptor("art1", category="artifact"))
    return r


class TestArtifactRuntimePipeline:
    def test_route(self):
        p = ArtifactRuntimePipeline(_registry())
        assert p.route() == INTEGRATION_ROUTE
        assert len(INTEGRATION_ROUTE) == 14
        assert INTEGRATION_ROUTE[5] == "audit"
        assert INTEGRATION_ROUTE[6] == "artifact"
        assert INTEGRATION_ROUTE[7] == "memory"
        assert INTEGRATION_ROUTE[-1] == "execution_preview"

    def test_container_index(self):
        assert ArtifactRuntimePipeline(_registry()).describe_artifact_stage() == 6

    def test_run_ok(self):
        run = ArtifactRuntimePipeline(_registry()).run("art1")
        assert run.ok is True
        assert run.external_calls == 0
        assert len(run.stages) == 14

    def test_run_stages(self):
        run = ArtifactRuntimePipeline(_registry()).run("art1")
        names = [s.name for s in run.stages]
        assert names == list(INTEGRATION_ROUTE)


class TestArtifactRuntimePipelineRun:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactRuntimePipelineRun().ok = False


class TestArtifactIntegrationStage:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactIntegrationStage("x").ok = False


class TestArtifactRuntimeReporter:
    def test_report(self):
        rep = ArtifactRuntimeReporter(_registry()).report()
        assert rep.total_artifact == 1
        assert rep.ready is True
        assert rep.external_calls == 0
        assert rep.no_storage is True
        assert rep.no_publish is True
        assert list(rep.route) == list(INTEGRATION_ROUTE)


class TestArtifactRuntimeReport:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactRuntimeReport().ready = False


class TestArtifactRuntimeManifest:
    def test_version(self):
        m = ArtifactRuntimeManifest()
        assert m.version == "23.0.0"
        assert m.phase == "XXIII"

    def test_integrated(self):
        m = ArtifactRuntimeManifest()
        # artifact tidak di daftar karena itu dirinya sendiri
        assert "artifact" not in m.integrated_runtimes
        assert "audit" in m.integrated_runtimes
        assert len(m.integrated_runtimes) == 12

    def test_properties(self):
        m = ArtifactRuntimeManifest()
        assert m.preview_only is True
        assert m.no_storage is True
        assert m.no_publish is True
        assert m.immutable is True
        assert m.no_execute is True
        assert m.external_calls == 0

    def test_immutable(self):
        m = ArtifactRuntimeManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestArtifactRuntimeSummarizer:
    def test_summarize(self):
        s = ArtifactRuntimeSummarizer().summarize()
        assert s.total_stages == 14
        assert s.container_index == 6
        assert s.integrated is True
        assert s.external_calls == 0


class TestArtifactRuntimeSummary:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactRuntimeSummary().integrated = False


class TestArtifactRuntimeRegistry:
    def test_from_route(self):
        reg = ArtifactRuntimeRegistry.from_route()
        assert reg.count == 14
        assert len(reg.entries) == 14

    def test_first(self):
        reg = ArtifactRuntimeRegistry.from_route()
        assert reg.entries[0].runtime == "mission"
        assert reg.entries[6].runtime == "artifact"

    def test_artifact_present(self):
        runtimes = [e.runtime for e in ArtifactRuntimeRegistry.from_route().entries]
        assert "artifact" in runtimes

    def test_immutable(self):
        reg = ArtifactRuntimeRegistry.from_route()
        with pytest.raises(FrozenInstanceError):
            reg.count = 1


class TestArtifactRuntimeRegistryEntry:
    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            ArtifactRuntimeRegistryEntry("x").integrated = False


class TestConversationIntegrationBridge:
    def test_five_queries(self):
        b = ConversationIntegrationBridge(_registry())
        assert b.query_1_route() == INTEGRATION_ROUTE
        assert b.query_2_status()["total_artifact"] == 1
        assert b.query_3_pipeline("art1")["ok"] is True
        assert b.query_4_report()["ready"] is True
        assert b.query_5_registry()["count"] == 14


class TestDashboardIntegrationBridge:
    def test_five_cards(self):
        b = DashboardIntegrationBridge(_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_container_card(self):
        cards = DashboardIntegrationBridge(_registry()).cards()
        assert "artifact stage index 6" in cards[2].value


class TestIntegrationImmutability:
    DTO = [ArtifactRuntimePipelineRun, ArtifactIntegrationStage,
           ArtifactRuntimeRegistry, ArtifactRuntimeRegistryEntry,
           ArtifactRuntimeManifest, ArtifactRuntimeReport,
           ArtifactRuntimeSummary]

    def test_all_frozen(self):
        for cls in self.DTO:
            assert cls.__dataclass_params__.frozen
