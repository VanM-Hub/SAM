# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 123 - Orchestration Foundation tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.orchestrator.orchestration_context import OrchestrationContext
from sam.orchestrator.orchestration_request import OrchestrationRequest
from sam.orchestrator.orchestration_descriptor import OrchestrationDescriptor
from sam.orchestrator.orchestration_registry import OrchestrationRegistry
from sam.orchestrator.orchestration_builder import OrchestrationBuilder, OrchestrationPlan
from sam.orchestrator.conversation_orchestration import ConversationOrchestrationBridge
from sam.orchestrator.dashboard_orchestration import DashboardOrchestrationBridge
from sam.connectors.dashboard_connector import ExecutionCard


def _registry():
    r = OrchestrationRegistry()
    r.register(OrchestrationDescriptor("execution", "Execution", pipeline_position=6))
    r.register(OrchestrationDescriptor("runtime_kernel", "Runtime Kernel", pipeline_position=7))
    r.register(OrchestrationDescriptor("connector", "Connector", pipeline_position=8))
    r.register(OrchestrationDescriptor("orchestration", "Orchestrator", pipeline_position=9))
    return r


# ---------- DTO immutability ----------
class TestContextImmutable:
    def test_frozen(self):
        c = OrchestrationContext("r1", "execution")
        with pytest.raises(FrozenInstanceError):
            c.source_runtime = "connector"


class TestRequestImmutable:
    def test_frozen(self):
        r = OrchestrationRequest("r1", "wf")
        with pytest.raises(FrozenInstanceError):
            r.priority = 9

    def test_preview_always(self):
        r = OrchestrationRequest("r1", "wf")
        assert r.is_preview is True


class TestDescriptorImmutable:
    def test_frozen(self):
        d = OrchestrationDescriptor("x", "X")
        with pytest.raises(FrozenInstanceError):
            d.name = "Y"


# ---------- Registry engine ----------
class TestOrchestrationRegistry:
    def test_register_and_count(self):
        r = _registry()
        assert r.count() == 4

    def test_get(self):
        r = _registry()
        assert r.get("connector").category == "runtime"

    def test_all_ordered_by_position(self):
        r = _registry()
        order = [d.runtime_id for d in r.all()]
        assert "execution" in order
        # position 9 last
        assert order[-1] == "orchestration"

    def test_missing_returns_none(self):
        r = _registry()
        assert r.get("nope") is None


# ---------- Builder engine ----------
class TestOrchestrationBuilder:
    def test_build_plans_known_chain(self):
        r = _registry()
        b = OrchestrationBuilder(r)
        plan = b.build(OrchestrationRequest("r1", "wf", runtimes=("execution", "connector")))
        assert plan is not None
        assert plan.chain == ("execution", "connector")
        assert plan.is_plan_only is True

    def test_build_unknown_dropped(self):
        r = _registry()
        b = OrchestrationBuilder(r)
        plan = b.build(OrchestrationRequest("r1", "wf", runtimes=("unknown", "connector")))
        assert plan.chain == ("connector",)

    def test_build_empty_returns_none(self):
        r = _registry()
        b = OrchestrationBuilder(r)
        assert b.build(OrchestrationRequest("r1", "wf")) is None

    def test_build_from_context(self):
        r = _registry()
        b = OrchestrationBuilder(r)
        ctx = OrchestrationContext("r1", "execution", runtimes=("execution", "orchestration"))
        req = OrchestrationRequest("r1", "wf", runtimes=("connector",))
        plan = b.build_from_context(req, ctx)
        assert plan.chain == ("execution", "orchestration")


# ---------- Conversation bridge (read-only) ----------
class TestConversationOrchestrationBridge:
    def test_count(self):
        b = ConversationOrchestrationBridge(_registry())
        assert b.count_runtimes() == 4

    def test_list(self):
        b = ConversationOrchestrationBridge(_registry())
        assert "Execution" in b.list_runtimes()

    def test_plan(self):
        b = ConversationOrchestrationBridge(_registry())
        plan = b.plan(OrchestrationRequest("r", "wf", runtimes=("connector",)))
        assert plan.chain == ("connector",)


# ---------- Dashboard bridge (read-only, 5 cards) ----------
class TestDashboardOrchestrationBridge:
    def test_five_cards(self):
        b = DashboardOrchestrationBridge(_registry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_verdict(self):
        b = DashboardOrchestrationBridge(_registry())
        assert "plan-only" in b.verdict_card().summary.lower()


# ---------- All DTOs frozen ----------
class TestAllFrozen:
    DTO_CLASSES = [
        OrchestrationContext,
        OrchestrationRequest,
        OrchestrationDescriptor,
        OrchestrationPlan,
    ]

    def test_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, cls.__name__
