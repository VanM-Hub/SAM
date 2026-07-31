"""Sprint 203 — Workflow Integration Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.workflow_runtime.integration.workflow_runtime_pipeline import (
    WorkflowRuntimePipeline, WorkflowRuntimePipelineRun, WorkflowIntegrationStage,
    INTEGRATION_ROUTE,
)
from sam.workflow_runtime.integration.workflow_runtime_report import (
    WorkflowRuntimeReport, WorkflowRuntimeReporter,
)
from sam.workflow_runtime.integration.workflow_runtime_manifest import (
    WorkflowRuntimeManifest,
)
from sam.workflow_runtime.integration.workflow_runtime_certification import (
    WorkflowRuntimeCertification, WorkflowRuntimeCertifier,
)
from sam.workflow_runtime.integration.workflow_runtime_registry import (
    WorkflowRuntimeRegistry, WorkflowRuntimeRegistryEntry,
)
from sam.workflow_runtime.integration.conversation_integration import (
    ConversationIntegrationBridge,
)
from sam.workflow_runtime.integration.dashboard_integration import (
    DashboardIntegrationBridge,
)
from sam.workflow_runtime.foundation.workflow_registry import WorkflowRegistry
from sam.workflow_runtime.foundation.workflow_descriptor import WorkflowDescriptor
from sam.workflow_runtime.dashboard import WorkflowCard


def _registry():
    r = WorkflowRegistry()
    r.register(WorkflowDescriptor("wf1", "Onboard", category="process"))
    return r


class TestWorkflowRuntimePipeline:
    def test_route(self):
        p = WorkflowRuntimePipeline(_registry())
        assert p.route() == INTEGRATION_ROUTE
        assert INTEGRATION_ROUTE[0] == "mission"
        assert INTEGRATION_ROUTE[2] == "skill"
        assert INTEGRATION_ROUTE[3] == "workflow"
        assert INTEGRATION_ROUTE[4] == "memory"
        assert INTEGRATION_ROUTE[6] == "cognitive"
        assert INTEGRATION_ROUTE[-1] == "provider"

    def test_run_ok(self):
        p = WorkflowRuntimePipeline(_registry())
        run = p.run("wf1")
        assert run.ok is True
        assert run.external_calls == 0
        assert len(run.stages) == 11

    def test_run_order(self):
        p = WorkflowRuntimePipeline(_registry())
        run = p.run("wf1")
        names = [s.name for s in run.stages]
        assert names == ["mission", "agent", "skill", "workflow", "memory",
                         "knowledge", "cognitive", "orchestrator", "connector",
                         "provider", "execution_preview"]

    def test_run_missing(self):
        p = WorkflowRuntimePipeline(WorkflowRegistry())
        run = p.run("nope")
        assert run.ok is False
        assert run.external_calls == 0
        assert len(run.stages) == 4


class TestWorkflowRuntimePipelineRun:
    def test_default(self):
        assert WorkflowRuntimePipelineRun().ok is False

    def test_immutable(self):
        run = WorkflowRuntimePipelineRun()
        with pytest.raises(FrozenInstanceError):
            run.ok = True


class TestWorkflowIntegrationStage:
    def test_immutable(self):
        s = WorkflowIntegrationStage("mission")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestWorkflowRuntimeReporter:
    def test_report(self):
        rep = WorkflowRuntimeReporter(_registry()).report()
        assert rep.total_workflow == 1
        assert rep.ready is True
        assert rep.external_calls == 0
        assert rep.route == INTEGRATION_ROUTE


class TestWorkflowRuntimeReport:
    def test_immutable(self):
        rep = WorkflowRuntimeReport()
        with pytest.raises(FrozenInstanceError):
            rep.ready = True


class TestWorkflowRuntimeManifest:
    def test_integrated(self):
        m = WorkflowRuntimeManifest()
        assert len(m.integrated_runtimes) == 9
        # workflow tidak ada di daftar karena itu dirinya sendiri
        assert "workflow" not in m.integrated_runtimes
        assert "cognitive" in m.integrated_runtimes
        assert "provider" in m.integrated_runtimes

    def test_no_inference(self):
        assert WorkflowRuntimeManifest().no_inference is True

    def test_immutable(self):
        m = WorkflowRuntimeManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestWorkflowRuntimeCertifier:
    def test_certify(self):
        c = WorkflowRuntimeCertifier().certify()
        assert c.certified is True
        assert c.score == 100.0
        assert c.no_layer_violations is True
        assert c.no_mutable_dto is True
        assert c.no_write is True
        assert c.no_inference is True
        assert c.external_calls_zero is True
        assert len(c.checks) == 7


class TestWorkflowRuntimeCertification:
    def test_default(self):
        c = WorkflowRuntimeCertification()
        assert c.certified is False

    def test_immutable(self):
        c = WorkflowRuntimeCertification()
        with pytest.raises(FrozenInstanceError):
            c.certified = True


class TestWorkflowRuntimeRegistry:
    def test_from_route(self):
        reg = WorkflowRuntimeRegistry.from_route()
        assert reg.count == 10
        assert len(reg.entries) == 10

    def test_first_runtime(self):
        reg = WorkflowRuntimeRegistry.from_route()
        assert reg.entries[0].runtime == "mission"
        assert reg.entries[0].integrated is True

    def test_workflow_present(self):
        reg = WorkflowRuntimeRegistry.from_route()
        runtimes = [e.runtime for e in reg.entries]
        assert "workflow" in runtimes

    def test_immutable(self):
        reg = WorkflowRuntimeRegistry.from_route()
        with pytest.raises(FrozenInstanceError):
            reg.count = 1


class TestWorkflowRuntimeRegistryEntry:
    def test_immutable(self):
        e = WorkflowRuntimeRegistryEntry("x")
        with pytest.raises(FrozenInstanceError):
            e.integrated = False


class TestConversationIntegrationBridge:
    def test_5_queries(self):
        b = ConversationIntegrationBridge(_registry())
        assert b.query_1_route() == INTEGRATION_ROUTE
        assert b.query_2_status()["total_workflow"] == 1
        assert b.query_3_pipeline("wf1")["ok"] is True
        assert b.query_4_report()["ready"] is True
        assert b.query_5_registry()["count"] == 10


class TestDashboardIntegrationBridge:
    def test_five_cards(self):
        b = DashboardIntegrationBridge(_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, WorkflowCard) for c in cards)

    def test_verdict(self):
        b = DashboardIntegrationBridge(_registry())
        assert b.verdict_card().verdict == "certified"


class TestIntegrationImmutability:
    DTO_CLASSES = [
        WorkflowRuntimePipelineRun, WorkflowIntegrationStage, WorkflowRuntimeReport,
        WorkflowRuntimeManifest, WorkflowRuntimeCertification,
        WorkflowRuntimeRegistry, WorkflowRuntimeRegistryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
