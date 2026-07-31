"""Sprint 161 — Transition Monitor Tests."""
import pytest
from dataclasses import FrozenInstanceError

from sam.agent.monitor.transition_monitor import TransitionMonitor, TransitionStatus
from sam.agent.monitor.runtime_status import RuntimeStatus, RuntimeStatusView
from sam.agent.monitor.runtime_progress import RuntimeProgress
from sam.agent.monitor.runtime_health import RuntimeHealth, RuntimeHealthCheck
from sam.agent.monitor.runtime_summary import RuntimeSummary, RuntimeSummarizer
from sam.agent.monitor.conversation_monitor import ConversationMonitorBridge
from sam.agent.monitor.dashboard_monitor import DashboardMonitorBridge
from sam.agent.state.state_machine import StateMachine, CREATED, RUNNING, COMPLETED
from sam.agent.state.transition_history import TransitionHistory, TransitionEvent
from sam.agent.coordinator.runtime_registry import RuntimeRegistry
from sam.agent.coordinator.runtime_queue import RuntimeQueue
from sam.agent.dashboard.agent_dashboard import ExecutionCard


def _monitor(pipeline_length=3):
    m = StateMachine()
    m.create("m1")
    h = TransitionHistory()
    q = RuntimeQueue()
    q.enqueue_many(["guardian", "decision", "execution"])
    return TransitionMonitor(m, h, q, pipeline_length), m, h


class TestTransitionMonitor:
    def test_status_initial(self):
        mon, m, h = _monitor()
        st = mon.status("m1")
        assert st.state == CREATED
        assert st.completed_steps == 0
        assert st.remaining_steps == 3

    def test_status_after_running(self):
        mon, m, h = _monitor()
        m.transition("m1", "Preparing")
        m.transition("m1", RUNNING)
        h.record(TransitionEvent("m1", CREATED, "Preparing"))
        h.record(TransitionEvent("m1", "Preparing", RUNNING))
        st = mon.status("m1")
        assert st.state == RUNNING
        assert st.current_runtime == "guardian"

    def test_waiting_reason(self):
        mon, m, h = _monitor()
        m.transition("m1", "Preparing")
        m.transition("m1", RUNNING)
        m.transition("m1", "Waiting")
        st = mon.status("m1")
        assert "waiting" in st.waiting_reason.lower()

    def test_progress_percent(self):
        mon, m, h = _monitor(pipeline_length=4)
        h.record(TransitionEvent("m1", "A", "B"))
        st = mon.status("m1")
        assert st.progress_percent == 25


class TestTransitionStatus:
    def test_default(self):
        assert TransitionStatus("m1").state == "Created"

    def test_immutable(self):
        st = TransitionStatus("m1")
        with pytest.raises(FrozenInstanceError):
            st.state = RUNNING


class TestRuntimeStatus:
    def test_view(self):
        reg = RuntimeRegistry()
        reg.register_many(["guardian"])
        v = RuntimeStatusView(reg)
        st = v.status("guardian")
        assert st.available is True

    def test_missing(self):
        v = RuntimeStatusView(RuntimeRegistry())
        assert v.status("nope").available is False

    def test_all(self):
        reg = RuntimeRegistry()
        reg.register_many(["a", "b"])
        v = RuntimeStatusView(reg)
        assert len(v.all_status()) == 2

    def test_immutable(self):
        st = RuntimeStatus("a")
        with pytest.raises(FrozenInstanceError):
            st.available = False


class TestRuntimeProgress:
    def test_percent(self):
        p = RuntimeProgress("m1", completed=2, total=4)
        assert p.percent == 50

    def test_done(self):
        assert RuntimeProgress("m1", completed=4, total=4).done is True
        assert RuntimeProgress("m1", completed=1, total=4).done is False

    def test_zero_total(self):
        assert RuntimeProgress("m1").percent == 0

    def test_immutable(self):
        p = RuntimeProgress("m1")
        with pytest.raises(FrozenInstanceError):
            p.completed = 1


class TestRuntimeHealth:
    def test_healthy(self):
        reg = RuntimeRegistry()
        reg.register_many(["a", "b"])
        h = RuntimeHealthCheck(reg).check()
        assert h.healthy is True
        assert h.total == 2
        assert h.available == 2

    def test_immutable(self):
        h = RuntimeHealth()
        with pytest.raises(FrozenInstanceError):
            h.healthy = False


class TestRuntimeSummarizer:
    def test_summary(self):
        m = StateMachine()
        m.create("m1")
        m.create("m2")
        s = RuntimeSummarizer(m).summary()
        assert s.total_missions == 2
        assert s.state_counts["Created"] == 2
        assert s.external_calls == 0


class TestRuntimeSummary:
    def test_default(self):
        assert RuntimeSummary().external_calls == 0


class TestConversationMonitorBridge:
    def test_show_progress(self):
        mon, m, h = _monitor(pipeline_length=4)
        h.record(TransitionEvent("m1", "A", "B"))
        b = ConversationMonitorBridge(mon)
        p = b.show_progress("m1")
        assert p["completed"] == 1
        assert p["remaining"] == 3

    def test_waiting_reason(self):
        mon, m, h = _monitor()
        b = ConversationMonitorBridge(mon)
        assert b.show_waiting_reason("m1") == ""

    def test_summary(self):
        mon, m, h = _monitor()
        b = ConversationMonitorBridge(mon, RuntimeSummarizer(m))
        assert b.show_summary()["total_missions"] == 1


class TestDashboardMonitorBridge:
    def test_five_cards(self):
        mon, m, h = _monitor()
        b = DashboardMonitorBridge(mon)
        cards = b.cards("m1")
        assert len(cards) == 5
        assert all(isinstance(c, ExecutionCard) for c in cards)

    def test_overview(self):
        mon, m, h = _monitor()
        b = DashboardMonitorBridge(mon)
        assert b.overview_card().card_id == "monitor.state"


class TestMonitorImmutability:
    DTO_CLASSES = [
        TransitionStatus, RuntimeStatus, RuntimeProgress,
        RuntimeHealth, RuntimeSummary,
    ]

    def test_all_frozen(self):
        for cls in self.DTO_CLASSES:
            assert cls.__dataclass_params__.frozen, f"{cls.__name__} should be frozen"
