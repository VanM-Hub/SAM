"""Sprint 219 — Audit Integration Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.audit_runtime.integration.audit_runtime_pipeline import (
    AuditRuntimePipeline, AuditRuntimePipelineRun, AuditIntegrationStage,
    INTEGRATION_ROUTE,
)
from sam.audit_runtime.integration.audit_runtime_report import (
    AuditRuntimeReport, AuditRuntimeReporter,
)
from sam.audit_runtime.integration.audit_runtime_manifest import (
    AuditRuntimeManifest,
)
from sam.audit_runtime.integration.audit_runtime_certification import (
    AuditRuntimeCertification, AuditRuntimeCertifier,
)
from sam.audit_runtime.integration.audit_runtime_registry import (
    AuditRuntimeRegistry, AuditRuntimeRegistryEntry,
)
from sam.audit_runtime.integration.conversation_integration import (
    ConversationIntegrationBridge,
)
from sam.audit_runtime.integration.dashboard_integration import (
    DashboardIntegrationBridge,
)
from sam.audit_runtime.foundation.audit_registry import AuditRegistry
from sam.audit_runtime.foundation.audit_descriptor import AuditDescriptor
from sam.audit_runtime.dashboard import PolicyCard


def _registry():
    r = AuditRegistry()
    r = r.register(AuditDescriptor("aud1", category="security"))
    return r


class TestAuditRuntimePipeline:
    def test_route(self):
        p = AuditRuntimePipeline(_registry())
        assert p.route() == INTEGRATION_ROUTE
        assert INTEGRATION_ROUTE[4] == "policy"
        assert INTEGRATION_ROUTE[5] == "audit"
        assert INTEGRATION_ROUTE[6] == "memory"
        assert INTEGRATION_ROUTE[8] == "cognitive"
        assert INTEGRATION_ROUTE[-1] == "provider"

    def test_run_ok(self):
        run = AuditRuntimePipeline(_registry()).run("aud1")
        assert run.ok is True
        assert run.external_calls == 0
        assert len(run.stages) == 13

    def test_run_order(self):
        run = AuditRuntimePipeline(_registry()).run("aud1")
        names = [s.name for s in run.stages]
        assert names == ["mission", "agent", "skill", "workflow", "policy",
                         "audit", "memory", "knowledge", "cognitive",
                         "orchestrator", "connector", "provider",
                         "execution_preview"]

    def test_run_missing(self):
        run = AuditRuntimePipeline(AuditRegistry()).run("nope")
        assert run.ok is False
        assert run.external_calls == 0
        assert len(run.stages) == 6


class TestAuditRuntimePipelineRun:
    def test_immutable(self):
        r = AuditRuntimePipelineRun()
        with pytest.raises(FrozenInstanceError):
            r.ok = True


class TestAuditIntegrationStage:
    def test_immutable(self):
        s = AuditIntegrationStage("mission")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestAuditRuntimeReporter:
    def test_report(self):
        rep = AuditRuntimeReporter(_registry()).report()
        assert rep.total_audit == 1
        assert rep.ready is True
        assert rep.external_calls == 0
        assert rep.route == INTEGRATION_ROUTE


class TestAuditRuntimeReport:
    def test_immutable(self):
        rep = AuditRuntimeReport()
        with pytest.raises(FrozenInstanceError):
            rep.ready = True


class TestAuditRuntimeManifest:
    def test_integrated(self):
        m = AuditRuntimeManifest()
        assert len(m.integrated_runtimes) == 11
        # audit tidak ada di daftar karena itu dirinya sendiri
        assert "audit" not in m.integrated_runtimes
        assert "policy" in m.integrated_runtimes
        assert "cognitive" in m.integrated_runtimes

    def test_no_inference(self):
        assert AuditRuntimeManifest().no_inference is True

    def test_immutable(self):
        m = AuditRuntimeManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestAuditRuntimeCertifier:
    def test_certify(self):
        c = AuditRuntimeCertifier().certify()
        assert c.certified is True
        assert c.score == 100.0
        assert c.no_layer_violations is True
        assert c.no_write is True
        assert c.no_execute is True
        assert c.external_calls_zero is True
        assert len(c.checks) == 7


class TestAuditRuntimeCertification:
    def test_immutable(self):
        c = AuditRuntimeCertification()
        with pytest.raises(FrozenInstanceError):
            c.certified = True


class TestAuditRuntimeRegistry:
    def test_from_route(self):
        reg = AuditRuntimeRegistry.from_route()
        assert reg.count == 12
        assert len(reg.entries) == 12

    def test_first_runtime(self):
        reg = AuditRuntimeRegistry.from_route()
        assert reg.entries[0].runtime == "mission"
        assert reg.entries[0].integrated is True

    def test_audit_present(self):
        reg = AuditRuntimeRegistry.from_route()
        runtimes = [e.runtime for e in reg.entries]
        assert "audit" in runtimes

    def test_immutable(self):
        reg = AuditRuntimeRegistry.from_route()
        with pytest.raises(FrozenInstanceError):
            reg.count = 1


class TestAuditRuntimeRegistryEntry:
    def test_immutable(self):
        e = AuditRuntimeRegistryEntry("x")
        with pytest.raises(FrozenInstanceError):
            e.integrated = False


class TestConversationIntegrationBridge:
    def test_5_queries(self):
        b = ConversationIntegrationBridge(_registry())
        assert b.query_1_route() == INTEGRATION_ROUTE
        assert b.query_2_status()["total_audit"] == 1
        assert b.query_3_pipeline("aud1")["ok"] is True
        assert b.query_4_report()["ready"] is True
        assert b.query_5_registry()["count"] == 12


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
        AuditRuntimePipelineRun, AuditIntegrationStage, AuditRuntimeReport,
        AuditRuntimeManifest, AuditRuntimeCertification,
        AuditRuntimeRegistry, AuditRuntimeRegistryEntry,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
