"""Sprint 211 — Policy Integration Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.policy_runtime.integration.policy_runtime_pipeline import (
    PolicyRuntimePipeline, PolicyRuntimePipelineRun, PolicyIntegrationStage,
    INTEGRATION_ROUTE,
)
from sam.policy_runtime.integration.policy_runtime_report import (
    PolicyRuntimeReport, PolicyRuntimeReporter,
)
from sam.policy_runtime.integration.policy_runtime_manifest import (
    PolicyRuntimeManifest,
)
from sam.policy_runtime.integration.policy_runtime_certification import (
    PolicyRuntimeCertification, PolicyRuntimeCertifier,
)
from sam.policy_runtime.integration.policy_runtime_registry import (
    PolicyRuntimeRegistry, PolicyRuntimeRegistryEntry,
)
from sam.policy_runtime.integration.conversation_integration import (
    ConversationIntegrationBridge,
)
from sam.policy_runtime.integration.dashboard_integration import (
    DashboardIntegrationBridge,
)
from sam.policy_runtime.foundation.policy_registry import PolicyRegistry
from sam.policy_runtime.foundation.policy_descriptor import PolicyDescriptor
from sam.policy_runtime.dashboard import PolicyCard


def _registry():
    r = PolicyRegistry()
    r.register(PolicyDescriptor("pol1", "AccessControl", category="security"))
    return r


class TestPolicyRuntimePipeline:
    def test_route(self):
        p = PolicyRuntimePipeline(_registry())
        assert p.route() == INTEGRATION_ROUTE
        assert INTEGRATION_ROUTE[3] == "workflow"
        assert INTEGRATION_ROUTE[4] == "policy"
        assert INTEGRATION_ROUTE[5] == "memory"
        assert INTEGRATION_ROUTE[7] == "cognitive"
        assert INTEGRATION_ROUTE[-1] == "provider"

    def test_run_ok(self):
        p = PolicyRuntimePipeline(_registry())
        run = p.run("pol1")
        assert run.ok is True
        assert run.external_calls == 0
        assert len(run.stages) == 12

    def test_run_order(self):
        p = PolicyRuntimePipeline(_registry())
        run = p.run("pol1")
        names = [s.name for s in run.stages]
        assert names == ["mission", "agent", "skill", "workflow", "policy",
                         "memory", "knowledge", "cognitive", "orchestrator",
                         "connector", "provider", "execution_preview"]

    def test_run_missing(self):
        p = PolicyRuntimePipeline(PolicyRegistry())
        run = p.run("nope")
        assert run.ok is False
        assert run.external_calls == 0
        assert len(run.stages) == 5


class TestPolicyRuntimePipelineRun:
    def test_default(self):
        assert PolicyRuntimePipelineRun().ok is False

    def test_immutable(self):
        run = PolicyRuntimePipelineRun()
        with pytest.raises(FrozenInstanceError):
            run.ok = True


class TestPolicyIntegrationStage:
    def test_immutable(self):
        s = PolicyIntegrationStage("mission")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestPolicyRuntimeReporter:
    def test_report(self):
        rep = PolicyRuntimeReporter(_registry()).report()
        assert rep.total_policy == 1
        assert rep.ready is True
        assert rep.external_calls == 0
        assert rep.route == INTEGRATION_ROUTE


class TestPolicyRuntimeReport:
    def test_immutable(self):
        rep = PolicyRuntimeReport()
        with pytest.raises(FrozenInstanceError):
            rep.ready = True


class TestPolicyRuntimeManifest:
    def test_integrated(self):
        m = PolicyRuntimeManifest()
        assert len(m.integrated_runtimes) == 10
        # policy tidak ada di daftar karena itu dirinya sendiri
        assert "policy" not in m.integrated_runtimes
        assert "workflow" in m.integrated_runtimes
        assert "cognitive" in m.integrated_runtimes
        assert "provider" in m.integrated_runtimes

    def test_no_inference(self):
        assert PolicyRuntimeManifest().no_inference is True

    def test_immutable(self):
        m = PolicyRuntimeManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestPolicyRuntimeCertifier:
    def test_certify(self):
        c = PolicyRuntimeCertifier().certify()
        assert c.certified is True
        assert c.score == 100.0
        assert c.no_layer_violations is True
        assert c.no_mutable_dto is True
        assert c.no_write is True
        assert c.no_inference is True
        assert c.external_calls_zero is True
        assert len(c.checks) == 7


class TestPolicyRuntimeCertification:
    def test_default(self):
        c = PolicyRuntimeCertification()
        assert c.certified is False

    def test_immutable(self):
        c = PolicyRuntimeCertification()
        with pytest.raises(FrozenInstanceError):
            c.certified = True


class TestPolicyRuntimeRegistry:
    def test_from_route(self):
        reg = PolicyRuntimeRegistry.from_route()
        assert reg.count == 11
        assert len(reg.entries) == 11

    def test_first_runtime(self):
        reg = PolicyRuntimeRegistry.from_route()
        assert reg.entries[0].runtime == "mission"
        assert reg.entries[0].integrated is True

    def test_policy_present(self):
        reg = PolicyRuntimeRegistry.from_route()
        runtimes = [e.runtime for e in reg.entries]
        assert "policy" in runtimes

    def test_immutable(self):
        reg = PolicyRuntimeRegistry.from_route()
        with pytest.raises(FrozenInstanceError):
            reg.count = 1


class TestPolicyRuntimeRegistryEntry:
    def test_immutable(self):
        e = PolicyRuntimeRegistryEntry("x")
        with pytest.raises(FrozenInstanceError):
            e.integrated = False


class TestConversationIntegrationBridge:
    def test_5_queries(self):
        b = ConversationIntegrationBridge(_registry())
        assert b.query_1_route() == INTEGRATION_ROUTE
        assert b.query_2_status()["total_policy"] == 1
        assert b.query_3_pipeline("pol1")["ok"] is True
        assert b.query_4_report()["ready"] is True
        assert b.query_5_registry()["count"] == 11


class TestDashboardIntegrationBridge:
    def test_five_cards(self):
        b = DashboardIntegrationBridge(_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_verdict(self):
        b = DashboardIntegrationBridge(_registry())
        assert b.verdict_card().verdict == "certified"


class TestIntegrationImmutability:
    DTO_CLASSES = [
        PolicyRuntimePipelineRun, PolicyIntegrationStage, PolicyRuntimeReport,
        PolicyRuntimeManifest, PolicyRuntimeCertification,
        PolicyRuntimeRegistry, PolicyRuntimeRegistryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
