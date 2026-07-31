"""Sprint 195 — Cognitive Integration Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.cognitive_runtime.integration.cognitive_runtime_pipeline import (
    CognitiveRuntimePipeline, CognitiveRuntimePipelineRun, CognitiveIntegrationStage,
    INTEGRATION_ROUTE,
)
from sam.cognitive_runtime.integration.cognitive_runtime_report import (
    CognitiveRuntimeReport, CognitiveRuntimeReporter,
)
from sam.cognitive_runtime.integration.cognitive_runtime_manifest import (
    CognitiveRuntimeManifest,
)
from sam.cognitive_runtime.integration.cognitive_runtime_certification import (
    CognitiveRuntimeCertification, CognitiveRuntimeCertifier,
)
from sam.cognitive_runtime.integration.conversation_integration import (
    ConversationIntegrationBridge,
)
from sam.cognitive_runtime.integration.dashboard_integration import (
    DashboardIntegrationBridge,
)
from sam.cognitive_runtime.foundation.cognitive_registry import CognitiveRegistry
from sam.cognitive_runtime.foundation.cognitive_descriptor import CognitiveDescriptor
from sam.cognitive_runtime.dashboard import ExecutionCard


def _registry():
    r = CognitiveRegistry()
    r.register(CognitiveDescriptor("cog1", "Core", category="core"))
    return r


class TestCognitiveRuntimePipeline:
    def test_route(self):
        p = CognitiveRuntimePipeline(_registry())
        assert p.route() == INTEGRATION_ROUTE
        assert INTEGRATION_ROUTE[0] == "mission"
        assert INTEGRATION_ROUTE[4] == "knowledge"
        assert INTEGRATION_ROUTE[5] == "cognitive"
        assert INTEGRATION_ROUTE[-1] == "provider"

    def test_run_ok(self):
        p = CognitiveRuntimePipeline(_registry())
        run = p.run("cog1")
        assert run.ok is True
        assert run.external_calls == 0
        assert len(run.stages) == 10

    def test_run_order(self):
        p = CognitiveRuntimePipeline(_registry())
        run = p.run("cog1")
        names = [s.name for s in run.stages]
        assert names == ["mission", "agent", "skill", "memory", "knowledge",
                         "cognitive", "orchestrator", "connector", "provider",
                         "execution_preview"]

    def test_run_missing(self):
        p = CognitiveRuntimePipeline(CognitiveRegistry())
        run = p.run("nope")
        assert run.ok is False
        assert run.external_calls == 0
        assert len(run.stages) == 6


class TestCognitiveRuntimePipelineRun:
    def test_default(self):
        assert CognitiveRuntimePipelineRun().ok is False

    def test_immutable(self):
        run = CognitiveRuntimePipelineRun()
        with pytest.raises(FrozenInstanceError):
            run.ok = True


class TestCognitiveIntegrationStage:
    def test_immutable(self):
        s = CognitiveIntegrationStage("mission")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestCognitiveRuntimeReporter:
    def test_report(self):
        rep = CognitiveRuntimeReporter(_registry()).report()
        assert rep.total_cognitive == 1
        assert rep.ready is True
        assert rep.external_calls == 0
        assert rep.route == INTEGRATION_ROUTE


class TestCognitiveRuntimeReport:
    def test_immutable(self):
        rep = CognitiveRuntimeReport()
        with pytest.raises(FrozenInstanceError):
            rep.ready = True


class TestCognitiveRuntimeManifest:
    def test_integrated(self):
        m = CognitiveRuntimeManifest()
        assert len(m.integrated_runtimes) == 8
        assert "knowledge" in m.integrated_runtimes
        assert "provider" in m.integrated_runtimes

    def test_no_inference(self):
        assert CognitiveRuntimeManifest().no_inference is True

    def test_immutable(self):
        m = CognitiveRuntimeManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestCognitiveRuntimeCertifier:
    def test_certify(self):
        c = CognitiveRuntimeCertifier().certify()
        assert c.certified is True
        assert c.score == 100.0
        assert c.no_layer_violations is True
        assert c.no_mutable_dto is True
        assert c.no_write is True
        assert c.no_inference is True
        assert c.external_calls_zero is True
        assert len(c.checks) == 7


class TestCognitiveRuntimeCertification:
    def test_default(self):
        c = CognitiveRuntimeCertification()
        assert c.certified is False

    def test_immutable(self):
        c = CognitiveRuntimeCertification()
        with pytest.raises(FrozenInstanceError):
            c.certified = True


class TestConversationIntegrationBridge:
    def test_5_queries(self):
        b = ConversationIntegrationBridge(_registry())
        assert b.query_1_route() == INTEGRATION_ROUTE
        assert b.query_2_status()["total_cognitive"] == 1
        assert b.query_3_pipeline("cog1")["ok"] is True
        assert b.query_4_report()["ready"] is True
        assert b.query_5_certification()["certified"] is True


class TestDashboardIntegrationBridge:
    def test_five_cards(self):
        b = DashboardIntegrationBridge(_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        b = DashboardIntegrationBridge(_registry())
        assert b.verdict_card().verdict == "certified"


class TestIntegrationImmutability:
    DTO_CLASSES = [
        CognitiveRuntimePipelineRun, CognitiveIntegrationStage, CognitiveRuntimeReport,
        CognitiveRuntimeManifest, CognitiveRuntimeCertification,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
