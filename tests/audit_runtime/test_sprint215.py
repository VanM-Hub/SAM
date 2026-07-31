"""Sprint 215 — Audit Runtime Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.audit_runtime.runtime.audit_runtime import (
    AuditRuntime, AuditRunResult,
)
from sam.audit_runtime.runtime.audit_pipeline import (
    AuditPipeline, AuditPipelineRun, AuditStage,
)
from sam.audit_runtime.runtime.audit_engine import AuditEngine
from sam.audit_runtime.runtime.audit_summary import (
    AuditSummary, AuditSummarizer,
)
from sam.audit_runtime.runtime.audit_statistics import (
    AuditStatistics, AuditStatisticsCollector,
)
from sam.audit_runtime.runtime.conversation_runtime import (
    ConversationRuntimeBridge,
)
from sam.audit_runtime.runtime.dashboard_runtime import DashboardRuntimeBridge
from sam.audit_runtime.foundation.audit_registry import AuditRegistry
from sam.audit_runtime.foundation.audit_descriptor import AuditDescriptor
from sam.audit_runtime.dashboard import PolicyCard


def _registry():
    return AuditRegistry().register(
        AuditDescriptor("aud1", category="security")).register(
        AuditDescriptor("aud2", category="operations"))


class TestAuditRuntime:
    def test_run_ok(self):
        r = AuditRuntime().run(_registry(), "aud1")
        assert r.ok is True
        assert r.external_calls == 0

    def test_run_missing(self):
        r = AuditRuntime().run(AuditRegistry(), "nope")
        assert r.ok is False
        assert r.external_calls == 0

    def test_capabilities(self):
        c = AuditRuntime.capabilities()
        assert c["preview_only"] is True
        assert c["no_write"] is True
        assert c["no_execute"] is True
        assert c["external_calls"] == 0


class TestAuditRunResult:
    def test_default(self):
        assert AuditRunResult().ok is False

    def test_immutable(self):
        r = AuditRunResult()
        with pytest.raises(FrozenInstanceError):
            r.ok = True


class TestAuditPipeline:
    def test_run_ok(self):
        p = AuditPipeline().run(_registry(), "aud1")
        assert p.ok is True
        assert p.external_calls == 0
        names = [s.name for s in p.stages]
        assert names == ["descriptor", "audit_record", "builder", "preview"]

    def test_run_missing(self):
        p = AuditPipeline().run(AuditRegistry(), "nope")
        assert p.ok is False
        assert len(p.stages) == 1


class TestAuditPipelineRun:
    def test_immutable(self):
        p = AuditPipelineRun()
        with pytest.raises(FrozenInstanceError):
            p.ok = True


class TestAuditStage:
    def test_immutable(self):
        s = AuditStage("x")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestAuditEngine:
    def test_not_llm(self):
        e = AuditEngine()
        assert e.is_llm is False
        assert e.is_ai is False
        assert e.inference is False

    def test_info(self):
        assert AuditEngine().info()["preview_only"] is True

    def test_immutable(self):
        e = AuditEngine()
        with pytest.raises(FrozenInstanceError):
            e.is_llm = True


class TestAuditSummarizer:
    def test_summarize(self):
        s = AuditSummarizer().summarize(_registry())
        assert s.total == 2
        assert s.categories == ("operations", "security")


class TestAuditSummary:
    def test_immutable(self):
        s = AuditSummary()
        with pytest.raises(FrozenInstanceError):
            s.total = 1


class TestAuditStatisticsCollector:
    def test_collect(self):
        st = AuditStatisticsCollector().collect(_registry())
        assert st.total == 2
        assert st.per_category["security"] == 1
        assert st.per_category["operations"] == 1


class TestAuditStatistics:
    def test_immutable(self):
        st = AuditStatistics()
        with pytest.raises(FrozenInstanceError):
            st.total = 1


class TestConversationRuntimeBridge:
    def test_5_queries(self):
        b = ConversationRuntimeBridge(_registry())
        assert b.query_1_run("aud1")["ok"] is True
        assert b.query_1_run("aud1")["external_calls"] == 0
        assert b.query_2_pipeline("aud1")["stages"] == 4
        assert b.query_3_summary()["total"] == 2
        assert b.query_4_statistics()["total"] == 2
        assert b.query_5_capabilities()["external_calls"] == 0


class TestDashboardRuntimeBridge:
    def test_five_cards(self):
        b = DashboardRuntimeBridge(_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_verdict(self):
        b = DashboardRuntimeBridge(_registry())
        assert b.verdict_card().status == "preview_only"


class TestRuntimeImmutability:
    DTO_CLASSES = [
        AuditRunResult, AuditPipelineRun, AuditStage, AuditEngine,
        AuditSummary, AuditStatistics,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
