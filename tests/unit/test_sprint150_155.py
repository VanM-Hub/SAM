"""Sprint 150-155 — Provider Infrastructure Tests.

Discovery, Session, Routing, Monitoring, Runtime, Certification.
"""
import pytest
from dataclasses import FrozenInstanceError

from sam.providers.filesystem import FilesystemProvider
from sam.providers.shell import ShellProvider
from sam.providers.sqlite import SQLiteProvider
from sam.providers.docker import DockerProvider
from sam.providers.openclaw import OpenClawProvider
from sam.providers.registry import ProviderRegistry, ProviderBuilder

from sam.providers.discovery import ProviderDiscovery, DiscoveryCriterion, DiscoveryResult
from sam.providers.session import ProviderSession, SessionSummary, ProviderSessionStore
from sam.providers.routing import ProviderRouter, RoutingRule, RoutingDecision
from sam.providers.monitoring import ProviderMonitor, MetricSample, MonitoringReport
from sam.providers.runtime import (
    ProviderRuntime, ProviderRuntimePipeline, PipelineStep, PipelineResult,
    ProviderRuntimeReporter, RuntimeReport,
)
from sam.providers.certification import (
    ProviderCertifier, CertificationCriterion, CertificationResult,
)


def _full_registry():
    b = ProviderBuilder()
    for p in [FilesystemProvider(), ShellProvider(), SQLiteProvider(),
              DockerProvider(), OpenClawProvider()]:
        b.add(p)
    return b.build()


# ============================================================
# Discovery (150)
# ============================================================
class TestProviderDiscovery:
    def test_all(self):
        d = ProviderDiscovery(_full_registry())
        assert set(d.all()) == {"filesystem", "shell", "sqlite", "docker", "openclaw"}

    def test_of_type(self):
        d = ProviderDiscovery(_full_registry())
        assert d.of_type("docker") == ["docker"]

    def test_discover_by_operation(self):
        d = ProviderDiscovery(_full_registry())
        res = d.discover(DiscoveryCriterion(operation="read"))
        assert "filesystem" in res.provider_ids

    def test_discover_by_type(self):
        d = ProviderDiscovery(_full_registry())
        res = d.discover(DiscoveryCriterion(provider_type="shell"))
        assert res.provider_ids == ["shell"]

    def test_immutable(self):
        r = DiscoveryResult(DiscoveryCriterion())
        with pytest.raises(FrozenInstanceError):
            r.provider_ids = ["x"]


# ============================================================
# Session (151)
# ============================================================
class TestProviderSessionStore:
    def test_open(self):
        s = ProviderSessionStore()
        sess = s.open_session("s1", "filesystem")
        assert sess.open is True
        assert s.count() == 1

    def test_close(self):
        s = ProviderSessionStore()
        s.open_session("s1", "filesystem")
        assert s.close("s1") is True
        assert s.get("s1").open is False

    def test_close_missing(self):
        s = ProviderSessionStore()
        assert s.close("nope") is False

    def test_for_provider(self):
        s = ProviderSessionStore()
        s.open_session("s1", "filesystem")
        s.open_session("s2", "shell")
        assert len(s.for_provider("filesystem")) == 1

    def test_summary(self):
        s = ProviderSessionStore()
        s.open_session("s1", "filesystem")
        s.open_session("s2", "shell")
        s.close("s1")
        sm = s.summary()
        assert sm.total == 2
        assert sm.open == 1

    def test_immutable(self):
        with pytest.raises(FrozenInstanceError):
            s = ProviderSession("s1", "fs"); s.open = False


# ============================================================
# Routing (152)
# ============================================================
class TestProviderRouter:
    def test_capability_fallback(self):
        r = ProviderRouter(_full_registry())
        d = r.route("read")
        assert d.matched is True
        assert d.provider_id == "filesystem"

    def test_by_provider_id_rule(self):
        r = ProviderRouter(_full_registry())
        r.add_rule(RoutingRule("read", provider_id="logreader"))
        # no such provider -> falls back
        assert r.route("read").matched is True

    def test_no_match(self):
        r = ProviderRouter(_full_registry())
        d = r.route("unknown_op")
        assert d.matched is False
        assert d.provider_id is None


# ============================================================
# Monitoring (153)
# ============================================================
class TestProviderMonitor:
    def test_report(self):
        m = ProviderMonitor(_full_registry())
        rep = m.report()
        assert rep.total_providers == 5
        assert rep.healthy_count == 5
        assert rep.total_external_calls == 0

    def test_sample(self):
        m = ProviderMonitor(_full_registry())
        assert len(m.sample()) == 5


# ============================================================
# Runtime (154)
# ============================================================
class TestProviderRuntimePipeline:
    def test_run_ok(self):
        p = ProviderRuntimePipeline(_full_registry())
        res = p.run("read")
        assert res.ok is True
        assert res.provider_id == "filesystem"
        assert len(res.steps) == 3

    def test_run_no_match(self):
        p = ProviderRuntimePipeline(_full_registry())
        res = p.run("nope")
        assert res.ok is False


class TestProviderRuntimeReporter:
    def test_report(self):
        rep = ProviderRuntimeReporter(_full_registry()).report()
        assert rep.total_providers == 5
        assert rep.ready is True
        assert rep.types["docker"] == 1


# ============================================================
# Certification (155)
# ============================================================
class TestProviderCertifier:
    def test_certify(self):
        c = ProviderCertifier(_full_registry())
        res = c.certify("filesystem")
        assert res.certified is True
        assert res.passed_count == 4

    def test_certify_missing(self):
        c = ProviderCertifier(_full_registry())
        assert c.certify("nope").certified is False

    def test_certify_all(self):
        c = ProviderCertifier(_full_registry())
        assert len(c.certified_ids()) == 5


# ============================================================
# Immutability
# ============================================================
class TestInfraImmutability:
    DTO_CLASSES = [
        DiscoveryCriterion, DiscoveryResult,
        ProviderSession, SessionSummary,
        RoutingRule, RoutingDecision,
        MetricSample, MonitoringReport,
        PipelineStep, PipelineResult, RuntimeReport,
        CertificationCriterion, CertificationResult,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
