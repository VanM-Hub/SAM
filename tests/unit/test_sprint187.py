"""Sprint 187 — Knowledge Integration Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.knowledge_runtime.integration.knowledge_runtime_pipeline import (
    KnowledgeRuntimePipeline, KnowledgeRuntimePipelineRun, KnowledgeIntegrationStage,
    INTEGRATION_ROUTE,
)
from sam.knowledge_runtime.integration.knowledge_runtime_report import (
    KnowledgeRuntimeReport, KnowledgeRuntimeReporter,
)
from sam.knowledge_runtime.integration.knowledge_runtime_manifest import (
    KnowledgeRuntimeManifest,
)
from sam.knowledge_runtime.integration.knowledge_runtime_certification import (
    KnowledgeRuntimeCertification, KnowledgeRuntimeCertifier,
)
from sam.knowledge_runtime.integration.conversation_integration import (
    ConversationIntegrationBridge,
)
from sam.knowledge_runtime.integration.dashboard_integration import (
    DashboardIntegrationBridge,
)
from sam.knowledge_runtime.foundation.knowledge_registry import KnowledgeRegistry
from sam.knowledge_runtime.foundation.knowledge_descriptor import KnowledgeDescriptor
from sam.knowledge_runtime.foundation.knowledge_capability import KnowledgeCapability
from sam.knowledge_runtime.dashboard.knowledge_dashboard import ExecutionCard


def _registry():
    r = KnowledgeRegistry()
    r.register(KnowledgeDescriptor("kn1", "Domain", category="domain"))
    r.attach_capability(KnowledgeCapability("c1", "kn1", operations=["fact"]))
    return r


class TestKnowledgeRuntimePipeline:
    def test_route(self):
        p = KnowledgeRuntimePipeline(_registry())
        assert p.route() == INTEGRATION_ROUTE
        assert INTEGRATION_ROUTE[0] == "mission"
        assert INTEGRATION_ROUTE[3] == "memory"
        assert INTEGRATION_ROUTE[4] == "knowledge"
        assert INTEGRATION_ROUTE[-1] == "provider"

    def test_run_ok(self):
        p = KnowledgeRuntimePipeline(_registry())
        run = p.run("kn1")
        assert run.ok is True
        assert run.external_calls == 0
        assert len(run.stages) == 9

    def test_run_order(self):
        p = KnowledgeRuntimePipeline(_registry())
        run = p.run("kn1")
        names = [s.name for s in run.stages]
        assert names == ["mission", "agent", "skill", "memory", "knowledge",
                         "orchestrator", "connector", "provider",
                         "execution_preview"]

    def test_run_missing(self):
        p = KnowledgeRuntimePipeline(KnowledgeRegistry())
        run = p.run("nope")
        assert run.ok is False
        assert run.external_calls == 0
        assert len(run.stages) == 5


class TestKnowledgeRuntimePipelineRun:
    def test_default(self):
        assert KnowledgeRuntimePipelineRun().ok is False

    def test_immutable(self):
        run = KnowledgeRuntimePipelineRun()
        with pytest.raises(FrozenInstanceError):
            run.ok = True


class TestKnowledgeIntegrationStage:
    def test_immutable(self):
        s = KnowledgeIntegrationStage("mission")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestKnowledgeRuntimeReporter:
    def test_report(self):
        rep = KnowledgeRuntimeReporter(_registry()).report()
        assert rep.total_knowledge == 1
        assert rep.ready is True
        assert rep.external_calls == 0
        assert rep.route == INTEGRATION_ROUTE


class TestKnowledgeRuntimeReport:
    def test_immutable(self):
        rep = KnowledgeRuntimeReport()
        with pytest.raises(FrozenInstanceError):
            rep.ready = True


class TestKnowledgeRuntimeManifest:
    def test_integrated(self):
        m = KnowledgeRuntimeManifest()
        assert len(m.integrated_runtimes) == 7
        assert "knowledge" in m.integrated_runtimes or "memory" in m.integrated_runtimes
        assert "provider" in m.integrated_runtimes

    def test_no_inference(self):
        assert KnowledgeRuntimeManifest().no_inference is True

    def test_immutable(self):
        m = KnowledgeRuntimeManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestKnowledgeRuntimeCertifier:
    def test_certify(self):
        c = KnowledgeRuntimeCertifier().certify()
        assert c.certified is True
        assert c.score == 100.0
        assert c.no_layer_violations is True
        assert c.no_mutable_dto is True
        assert c.no_write is True
        assert c.no_inference is True
        assert c.external_calls_zero is True
        assert len(c.checks) == 7


class TestKnowledgeRuntimeCertification:
    def test_default(self):
        c = KnowledgeRuntimeCertification()
        assert c.certified is False

    def test_immutable(self):
        c = KnowledgeRuntimeCertification()
        with pytest.raises(FrozenInstanceError):
            c.certified = True


class TestConversationIntegrationBridge:
    def test_5_queries(self):
        b = ConversationIntegrationBridge(_registry())
        assert b.query_1_route() == INTEGRATION_ROUTE
        assert b.query_2_status()["total_knowledge"] == 1
        assert b.query_3_pipeline("kn1")["ok"] is True
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
        KnowledgeRuntimePipelineRun, KnowledgeIntegrationStage, KnowledgeRuntimeReport,
        KnowledgeRuntimeManifest, KnowledgeRuntimeCertification,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
