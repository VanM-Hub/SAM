"""Sprint 160 — Runtime Coordinator Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.agent.coordinator.runtime_request import RuntimeRequest
from sam.agent.coordinator.runtime_response import RuntimeResponse
from sam.agent.coordinator.runtime_queue import RuntimeQueue, RuntimeQueueEntry
from sam.agent.coordinator.runtime_registry import RuntimeRegistry, RuntimeEntry
from sam.agent.coordinator.runtime_coordinator import RuntimeCoordinator, CoordinatorDecision
from sam.agent.coordinator.conversation_coordinator import ConversationCoordinatorBridge
from sam.agent.coordinator.dashboard_coordinator import DashboardCoordinatorBridge
from sam.agent.dashboard.agent_dashboard import ExecutionCard


class TestRuntimeRequest:
    def test_default(self):
        r = RuntimeRequest("r1", "m1", "guardian")
        assert r.external_calls == 0
        assert r.operation == "advance"

    def test_immutable(self):
        r = RuntimeRequest("r1", "m1", "guardian")
        with pytest.raises(FrozenInstanceError):
            r.runtime_name = "decision"


class TestRuntimeResponse:
    def test_preview_default(self):
        assert RuntimeResponse("r1", "guardian").preview is True
        assert RuntimeResponse("r1", "guardian").external_calls == 0

    def test_immutable(self):
        r = RuntimeResponse("r1", "guardian")
        with pytest.raises(FrozenInstanceError):
            r.ok = False


class TestRuntimeQueue:
    def test_enqueue(self):
        q = RuntimeQueue()
        q.enqueue("guardian")
        assert q.count() == 1

    def test_enqueue_many(self):
        q = RuntimeQueue()
        q.enqueue_many(["a", "b", "c"])
        assert q.count() == 3

    def test_next_pending_order(self):
        q = RuntimeQueue()
        q.enqueue_many(["a", "b"])
        assert q.next_pending().runtime_name == "a"

    def test_mark_processed(self):
        q = RuntimeQueue()
        q.enqueue_many(["a", "b"])
        assert q.mark_processed("a") is True
        assert q.next_pending().runtime_name == "b"
        q.mark_processed("b")
        assert q.next_pending() is None

    def test_pending_count(self):
        q = RuntimeQueue()
        q.enqueue_many(["a", "b"])
        q.mark_processed("a")
        assert len(q.pending()) == 1

    def test_mark_missing(self):
        assert RuntimeQueue().mark_processed("zzz") is False


class TestRuntimeQueueEntry:
    def test_immutable(self):
        e = RuntimeQueueEntry("a", 0)
        with pytest.raises(FrozenInstanceError):
            e.processed = True


class TestRuntimeRegistry:
    def test_register(self):
        r = RuntimeRegistry()
        r.register_many(["guardian", "decision"])
        assert r.count() == 2
        assert r.has("guardian")

    def test_duplicate_rejected(self):
        r = RuntimeRegistry()
        assert r.register(RuntimeEntry("a"))
        assert not r.register(RuntimeEntry("a"))

    def test_names(self):
        r = RuntimeRegistry()
        r.register_many(["a", "b"])
        assert set(r.names()) == {"a", "b"}

    def test_preview_default(self):
        assert RuntimeEntry("a").preview_only is True

    def test_supports(self):
        r = RuntimeRegistry()
        r.register_many(["guardian"])
        req = RuntimeRequest("r1", "m1", "guardian")
        assert r.supports(req) is True
        assert r.supports(RuntimeRequest("r2", "m1", "nope")) is False


class TestRuntimeCoordinator:
    def _coord(self):
        reg = RuntimeRegistry()
        reg.register_many(["guardian", "decision"])
        q = RuntimeQueue()
        q.enqueue_many(["guardian", "decision"])
        return RuntimeCoordinator(reg, q)

    def test_determine_next(self):
        c = self._coord()
        d = c.determine_next("m1")
        assert d.matched is True
        assert d.next_runtime == "guardian"

    def test_advance(self):
        c = self._coord()
        d1 = c.determine_next("m1")
        assert d1.next_runtime == "guardian"

    def test_empty_queue(self):
        c = RuntimeCoordinator(RuntimeRegistry())
        d = c.determine_next("m1")
        assert d.matched is False

    def test_unregistered(self):
        reg = RuntimeRegistry()
        q = RuntimeQueue()
        q.enqueue("nope")
        c = RuntimeCoordinator(reg, q)
        d = c.determine_next("m1")
        assert d.matched is False


class TestCoordinatorDecision:
    def test_immutable(self):
        d = CoordinatorDecision("m1")
        with pytest.raises(FrozenInstanceError):
            d.matched = True


class TestConversationCoordinatorBridge:
    def test_current_runtime(self):
        reg = RuntimeRegistry()
        q = RuntimeQueue()
        q.enqueue("guardian")
        b = ConversationCoordinatorBridge(reg, q)
        assert b.show_current_runtime() == "guardian"

    def test_registry(self):
        reg = RuntimeRegistry()
        reg.register_many(["a", "b"])
        b = ConversationCoordinatorBridge(reg)
        assert set(b.show_registry()) == {"a", "b"}

    def test_pending(self):
        reg = RuntimeRegistry()
        q = RuntimeQueue()
        q.enqueue_many(["a", "b"])
        b = ConversationCoordinatorBridge(reg, q)
        assert b.show_pending() == 2


class TestDashboardCoordinatorBridge:
    def test_five_cards(self):
        b = DashboardCoordinatorBridge(RuntimeRegistry())
        cards = b.cards()
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        b = DashboardCoordinatorBridge(RuntimeRegistry())
        assert b.overview_card().verdict == "ready"


class TestCoordinatorImmutability:
    DTO_CLASSES = [
        RuntimeRequest, RuntimeResponse, RuntimeQueueEntry,
        RuntimeEntry, CoordinatorDecision,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
