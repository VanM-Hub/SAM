"""Sprint 179 — Memory Integration Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.memory.integration.memory_runtime_pipeline import (
    MemoryRuntimePipeline, MemoryRuntimePipelineRun, MemoryIntegrationStage,
    INTEGRATION_ROUTE,
)
from sam.memory.integration.memory_runtime_report import (
    MemoryRuntimeReport, MemoryRuntimeReporter,
)
from sam.memory.integration.memory_runtime_manifest import MemoryRuntimeManifest
from sam.memory.integration.memory_runtime_certification import (
    MemoryRuntimeCertification, MemoryRuntimeCertifier,
)
from sam.memory.integration.conversation_integration import ConversationIntegrationBridge
from sam.memory.integration.dashboard_integration import DashboardIntegrationBridge
from sam.memory.foundation.memory_registry import MemoryRegistry
from sam.memory.foundation.memory_descriptor import MemoryDescriptor
from sam.memory.foundation.memory_capability import MemoryCapability
from sam.memory.dashboard.memory_dashboard import ExecutionCard


def _registry():
    r = MemoryRegistry()
    r.register(MemoryDescriptor("mem1", "Short Term", category="short_term"))
    r.attach_capability(MemoryCapability("c1", "mem1", operations=["retain"]))
    return r


class TestMemoryRuntimePipeline:
    def test_route(self):
        p = MemoryRuntimePipeline(_registry())
        assert p.route() == INTEGRATION_ROUTE
        assert INTEGRATION_ROUTE[0] == "mission"
        assert INTEGRATION_ROUTE[2] == "skill"
        assert INTEGRATION_ROUTE[3] == "memory"
        assert INTEGRATION_ROUTE[-1] == "provider"

    def test_run_ok(self):
        p = MemoryRuntimePipeline(_registry())
        run = p.run("mem1")
        assert run.ok is True
        assert run.external_calls == 0
        assert len(run.stages) == 8

    def test_run_order(self):
        p = MemoryRuntimePipeline(_registry())
        run = p.run("mem1")
        names = [s.name for s in run.stages]
        assert names == ["mission", "agent", "skill", "memory",
                         "orchestrator", "connector", "provider",
                         "execution_preview"]

    def test_run_missing(self):
        p = MemoryRuntimePipeline(MemoryRegistry())
        run = p.run("nope")
        assert run.ok is False
        assert run.external_calls == 0
        assert len(run.stages) == 4


class TestMemoryRuntimePipelineRun:
    def test_default(self):
        assert MemoryRuntimePipelineRun().ok is False

    def test_immutable(self):
        run = MemoryRuntimePipelineRun()
        with pytest.raises(FrozenInstanceError):
            run.ok = True


class TestMemoryIntegrationStage:
    def test_immutable(self):
        s = MemoryIntegrationStage("mission")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestMemoryRuntimeReporter:
    def test_report(self):
        rep = MemoryRuntimeReporter(_registry()).report()
        assert rep.total_memories == 1
        assert rep.ready is True
        assert rep.external_calls == 0
        assert rep.route == INTEGRATION_ROUTE


class TestMemoryRuntimeReport:
    def test_immutable(self):
        rep = MemoryRuntimeReport()
        with pytest.raises(FrozenInstanceError):
            rep.ready = True


class TestMemoryRuntimeManifest:
    def test_integrated(self):
        m = MemoryRuntimeManifest()
        assert len(m.integrated_runtimes) == 6
        assert "memory" in m.integrated_runtimes or "skill" in m.integrated_runtimes
        assert "provider" in m.integrated_runtimes

    def test_preview(self):
        assert MemoryRuntimeManifest().preview_only is True

    def test_immutable(self):
        m = MemoryRuntimeManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestMemoryRuntimeCertifier:
    def test_certify(self):
        c = MemoryRuntimeCertifier().certify()
        assert c.certified is True
        assert c.score == 100.0
        assert c.no_layer_violations is True
        assert c.no_mutable_dto is True
        assert c.no_write is True
        assert c.external_calls_zero is True
        assert len(c.checks) == 7


class TestMemoryRuntimeCertification:
    def test_default(self):
        c = MemoryRuntimeCertification()
        assert c.certified is False

    def test_immutable(self):
        c = MemoryRuntimeCertification()
        with pytest.raises(FrozenInstanceError):
            c.certified = True


class TestConversationIntegrationBridge:
    def test_5_queries(self):
        b = ConversationIntegrationBridge(_registry())
        assert b.query_1_route() == INTEGRATION_ROUTE
        assert b.query_2_status()["total_memories"] == 1
        assert b.query_3_pipeline("mem1")["ok"] is True
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
        MemoryRuntimePipelineRun, MemoryIntegrationStage, MemoryRuntimeReport,
        MemoryRuntimeManifest, MemoryRuntimeCertification,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
