"""Sprint 207 — Policy Runtime Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.policy_runtime.runtime.policy_runtime import (
    PolicyRuntime, PolicyRunResult,
)
from sam.policy_runtime.runtime.policy_pipeline import (
    PolicyPipeline, PolicyPipelineRun, PolicyPipelineStage,
)
from sam.policy_runtime.runtime.policy_engine import (
    PolicyEngine, PolicyEngineInfo,
)
from sam.policy_runtime.runtime.policy_summary import (
    PolicySummary, PolicySummarizer,
)
from sam.policy_runtime.runtime.policy_statistics import (
    PolicyStatistics, PolicyStatisticsItem, PolicyStatisticsCollector,
)
from sam.policy_runtime.runtime.conversation_runtime import ConversationRuntimeBridge
from sam.policy_runtime.runtime.dashboard_runtime import DashboardRuntimeBridge
from sam.policy_runtime.foundation.policy_registry import PolicyRegistry
from sam.policy_runtime.foundation.policy_descriptor import PolicyDescriptor
from sam.policy_runtime.model.policy import Policy
from sam.policy_runtime.dashboard import PolicyCard


def _registry():
    r = PolicyRegistry()
    r.register(PolicyDescriptor("pol1", "AccessControl", category="security"))
    return r


class TestPolicyRuntime:
    def test_run_ok(self):
        r = PolicyRuntime(_registry()).run("pol1")
        assert r.ok is True
        assert r.policy_id == "pol1"
        assert r.external_calls == 0
        assert r.decided is False

    def test_run_missing(self):
        r = PolicyRuntime(PolicyRegistry()).run("nope")
        assert r.ok is False
        assert r.external_calls == 0

    def test_engine_info(self):
        info = PolicyRuntime(_registry()).engine_info()
        assert info["no_inference"] is True
        assert info["preview_only"] is True


class TestPolicyRunResult:
    def test_default(self):
        assert PolicyRunResult().external_calls == 0

    def test_immutable(self):
        r = PolicyRunResult()
        with pytest.raises(FrozenInstanceError):
            r.ok = False


class TestPolicyPipeline:
    def test_stages(self):
        p = PolicyPipeline(_registry())
        assert p.stages() == ["descriptor", "policy", "builder", "preview"]

    def test_run_ok(self):
        p = PolicyPipeline(_registry()).run("pol1")
        assert p.ok is True
        assert len(p.stages) == 4
        assert p.external_calls == 0

    def test_run_missing(self):
        p = PolicyPipeline(PolicyRegistry()).run("nope")
        assert p.ok is False
        assert len(p.stages) == 1


class TestPolicyPipelineRun:
    def test_default(self):
        assert PolicyPipelineRun().ok is False

    def test_immutable(self):
        p = PolicyPipelineRun()
        with pytest.raises(FrozenInstanceError):
            p.ok = True


class TestPolicyPipelineStage:
    def test_immutable(self):
        s = PolicyPipelineStage("x")
        with pytest.raises(FrozenInstanceError):
            s.ok = False


class TestPolicyEngine:
    def test_info(self):
        info = PolicyEngine().info()
        assert info.no_inference is True
        assert info.is_llm is False
        assert info.is_ai is False
        assert info.deterministic is True


class TestPolicyEngineInfo:
    def test_immutable(self):
        i = PolicyEngineInfo()
        with pytest.raises(FrozenInstanceError):
            i.no_inference = False


class TestPolicySummarizer:
    def test_summarize(self):
        pol = Policy("pol1", rules=["r1"], scope="system")
        s = PolicySummarizer().summarize(pol)
        assert s.policy_id == "pol1"
        assert s.rule_count == 1
        assert s.scope == "system"


class TestPolicySummary:
    def test_immutable(self):
        s = PolicySummary()
        with pytest.raises(FrozenInstanceError):
            s.rule_count = 1


class TestPolicyStatisticsCollector:
    def test_collect(self):
        s = PolicyStatisticsCollector(_registry()).collect()
        assert s.total == 1
        assert s.registered == 1


class TestPolicyStatistics:
    def test_default(self):
        assert PolicyStatistics().total == 0

    def test_immutable(self):
        s = PolicyStatistics()
        with pytest.raises(FrozenInstanceError):
            s.total = 1


class TestPolicyStatisticsItem:
    def test_default(self):
        assert PolicyStatisticsItem().registered is False


class TestConversationRuntimeBridge:
    def test_5_queries(self):
        b = ConversationRuntimeBridge(_registry())
        assert b.query_1_run("pol1")["ok"] is True
        assert b.query_2_pipeline("pol1")["ok"] is True
        assert len(b.query_3_stages()) == 4
        assert b.query_4_statistics()["total"] == 1
        assert b.query_5_engine()["is_llm"] is False


class TestDashboardRuntimeBridge:
    def test_five_cards(self):
        b = DashboardRuntimeBridge(_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, PolicyCard) for c in cards)

    def test_overview(self):
        b = DashboardRuntimeBridge(_registry())
        assert b.overview_card().verdict == "ready"


class TestRuntimeImmutability:
    DTO_CLASSES = [
        PolicyRunResult, PolicyPipelineRun, PolicyPipelineStage,
        PolicyEngineInfo, PolicySummary, PolicyStatistics,
        PolicyStatisticsItem,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
