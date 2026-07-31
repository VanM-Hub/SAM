"""Sprint 171 — Runtime Integration Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.skills.integration.skill_runtime_pipeline import (
    SkillRuntimePipeline, SkillRuntimePipelineRun, IntegrationStage, INTEGRATION_ROUTE,
)
from sam.skills.integration.skill_runtime_report import (
    SkillRuntimeReport, SkillRuntimeReporter,
)
from sam.skills.integration.skill_runtime_manifest import SkillRuntimeManifest
from sam.skills.integration.skill_runtime_certification import (
    SkillRuntimeCertification, SkillRuntimeCertifier,
)
from sam.skills.integration.conversation_integration import ConversationIntegrationBridge
from sam.skills.integration.dashboard_integration import DashboardIntegrationBridge
from sam.skills.foundation.skill_registry import SkillRegistry
from sam.skills.foundation.skill_descriptor import SkillDescriptor
from sam.skills.foundation.skill_capability import SkillCapability
from sam.skills.dashboard.skill_dashboard import ExecutionCard


def _registry():
    r = SkillRegistry()
    r.register(SkillDescriptor("skill1", "Read", category="io"))
    r.attach_capability(SkillCapability("c1", "skill1", operations=["read"]))
    return r


class TestSkillRuntimePipeline:
    def test_route(self):
        p = SkillRuntimePipeline(_registry())
        assert p.route() == INTEGRATION_ROUTE
        assert INTEGRATION_ROUTE[0] == "mission"
        assert INTEGRATION_ROUTE[-1] == "provider"

    def test_run_ok(self):
        p = SkillRuntimePipeline(_registry())
        run = p.run("skill1")
        assert run.ok is True
        assert run.external_calls == 0
        assert len(run.stages) == 7

    def test_run_order(self):
        p = SkillRuntimePipeline(_registry())
        run = p.run("skill1")
        names = [s.name for s in run.stages]
        assert names == ["mission", "agent", "skill", "orchestrator",
                         "connector", "provider", "execution_preview"]

    def test_run_missing(self):
        p = SkillRuntimePipeline(SkillRegistry())
        run = p.run("nope")
        assert run.ok is False
        assert run.external_calls == 0


class TestSkillRuntimePipelineRun:
    def test_default(self):
        assert SkillRuntimePipelineRun().ok is False

    def test_immutable(self):
        run = SkillRuntimePipelineRun()
        with pytest.raises(FrozenInstanceError):
            run.ok = True


class TestIntegrationStage:
    def test_immutable(self):
        s = IntegrationStage("mission")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestSkillRuntimeReporter:
    def test_report(self):
        rep = SkillRuntimeReporter(_registry()).report()
        assert rep.total_skills == 1
        assert rep.ready is True
        assert rep.external_calls == 0
        assert rep.route == INTEGRATION_ROUTE


class TestSkillRuntimeReport:
    def test_immutable(self):
        rep = SkillRuntimeReport()
        with pytest.raises(FrozenInstanceError):
            rep.ready = True


class TestSkillRuntimeManifest:
    def test_integrated(self):
        m = SkillRuntimeManifest()
        assert len(m.integrated_runtimes) == 5
        assert "mission" in m.integrated_runtimes
        assert "provider" in m.integrated_runtimes

    def test_preview(self):
        assert SkillRuntimeManifest().preview_only is True

    def test_immutable(self):
        m = SkillRuntimeManifest()
        with pytest.raises(FrozenInstanceError):
            m.version = "x"


class TestSkillRuntimeCertifier:
    def test_certify(self):
        c = SkillRuntimeCertifier().certify()
        assert c.certified is True
        assert c.score == 100.0
        assert c.no_layer_violations is True
        assert c.no_mutable_dto is True
        assert c.external_calls_zero is True
        assert len(c.checks) == 7


class TestSkillRuntimeCertification:
    def test_default(self):
        c = SkillRuntimeCertification()
        assert c.certified is False

    def test_immutable(self):
        c = SkillRuntimeCertification()
        with pytest.raises(FrozenInstanceError):
            c.certified = True


class TestConversationIntegrationBridge:
    def test_5_queries(self):
        b = ConversationIntegrationBridge(_registry())
        # Query 1
        assert b.query_1_route() == INTEGRATION_ROUTE
        # Query 2
        assert b.query_2_status()["total_skills"] == 1
        # Query 3
        assert b.query_3_pipeline("skill1")["ok"] is True
        # Query 4
        assert b.query_4_report()["ready"] is True
        # Query 5
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
        SkillRuntimePipelineRun, IntegrationStage, SkillRuntimeReport,
        SkillRuntimeManifest, SkillRuntimeCertification,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
