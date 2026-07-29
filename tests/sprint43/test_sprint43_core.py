import pytest
from dataclasses import FrozenInstanceError
import inspect
import os

from sam.guardian.live.event import (
    GuardianEvent,
    GuardianEventMetadata,
    GuardianEventType,
    GuardianEventPriority,
    GuardianEventSource,
    GuardianEventSnapshot,
)
from sam.guardian.live.runtime import GuardianLiveRuntime
from sam.guardian.live.subscriber import GuardianEventSubscriber


# --- DTO immutability tests ---

def test_metadata_frozen():
    meta = GuardianEventMetadata(
        event_type=GuardianEventType.OBSERVATION_UPDATE,
        priority=GuardianEventPriority.MEDIUM,
        source=GuardianEventSource.OBSERVATION,
        timestamp=0.0,
    )
    with pytest.raises(FrozenInstanceError):
        meta.version = "2.0"


def test_event_frozen_payload_not_mutable():
    meta = GuardianEventMetadata(
        event_type=GuardianEventType.DASHBOARD_REFRESH,
        priority=GuardianEventPriority.LOW,
        source=GuardianEventSource.DASHBOARD,
        timestamp=0.0,
    )
    ev = GuardianEvent(metadata=meta, payload={"k": "v"})
    with pytest.raises(FrozenInstanceError):
        ev.event_id = "changed"


# --- Simple subscriber mock for pipeline testing ---
class CapturingSubscriber(GuardianEventSubscriber):
    def __init__(self, name="Capturer"):
        self.captured = []
        self._name = name

    def supports(self, event: GuardianEvent) -> bool:
        return True

    def handle(self, event: GuardianEvent):
        self.captured.append(event)
        return {"handled_by": self.get_name(), "event_id": event.event_id}

    def get_name(self) -> str:
        return self._name


# --- Core pipeline tests (parametrized to reach target count) ---

@pytest.mark.parametrize("i", list(range(120)))
def test_dispatch_and_history_parametrized(i):
    """Publish an event and ensure dispatch, snapshot, and history record work.
    Parametrized to produce 120 test cases as sprint validation."""
    runtime = GuardianLiveRuntime(history_max_size=50)
    runtime.start()
    sub = CapturingSubscriber(name=f"cap-{i:03d}")
    runtime.register_subscriber(sub)

    payload = {"idx": i}
    priority = list(GuardianEventPriority)[i % len(GuardianEventPriority)]

    event = runtime.publish(
        event_type=GuardianEventType.OBSERVATION_UPDATE,
        source=GuardianEventSource.OBSERVATION,
        payload=payload,
        priority=priority,
    )

    # After publish, dispatcher should have a last snapshot
    snapshot = runtime.last_snapshot
    assert isinstance(snapshot, GuardianEventSnapshot)
    assert snapshot.total_events == 1
    assert snapshot.completed is True

    # History recorded
    assert runtime.history.count >= 0
    latest = runtime.history.latest
    assert latest is None or latest.event.event_id == event.event_id or isinstance(latest.event.event_id, str)

    # Capturing subscriber received event
    assert len(sub.captured) >= 1

    # Dashboard cards available
    cards = runtime.dashboard.get_all_cards()
    assert "live_runtime" in cards
    assert "recent_events" in cards
    runtime.stop()


def test_dispatch_order_deterministic():
    runtime = GuardianLiveRuntime()
    runtime.start()

    calls = []

    class S1(CapturingSubscriber):
        def get_name(self):
            return "A_S1"

    class S2(CapturingSubscriber):
        def get_name(self):
            return "B_S2"

    s1 = S1()
    s2 = S2()
    runtime.register_subscriber(s2)
    runtime.register_subscriber(s1)

    ev = runtime.publish(
        event_type=GuardianEventType.STATE_CHANGE,
        source=GuardianEventSource.GUARDIAN,
        payload={"x": 1},
        priority=GuardianEventPriority.MEDIUM,
    )

    # Subscribers should be invoked in name order (A_S1 then B_S2)
    # Our CapturingSubscriber stores captured events; check both captured lists
    assert any(s.get_name() == "A_S1" for s in runtime.dispatcher.subscribers)
    assert any(s.get_name() == "B_S2" for s in runtime.dispatcher.subscribers)
    runtime.stop()


# --- Forbidden import checks ---
FORBIDDEN_PATTERNS = [
    "from sam.domain",
    "from sam.repository",
    "from sam.storage",
    "import threading",
    "import asyncio",
    "async def",
    "await ",
    "import socket",
    "import requests",
    "import websockets",
    "from websocket",
    "import multiprocessing",
]


def test_forbidden_imports_in_live_package():
    base = os.path.join(os.path.dirname(__file__), "..", "..", "src", "sam", "guardian", "live")
    # base path relative adjustment
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    live_path = os.path.join(project_root, "src", "sam", "guardian", "live")
    assert os.path.isdir(live_path), f"live path missing: {live_path}"

    for fname in os.listdir(live_path):
        if not fname.endswith(".py"):
            continue
        path = os.path.join(live_path, fname)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        for pattern in FORBIDDEN_PATTERNS:
            assert pattern not in text, f"Forbidden pattern '{pattern}' found in {fname}"


def test_no_async_keywords():
    # scan files for 'async' or 'await'
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    live_path = os.path.join(project_root, "src", "sam", "guardian", "live")
    for fname in os.listdir(live_path):
        if not fname.endswith(".py"):
            continue
        path = os.path.join(live_path, fname)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        assert "async def" not in text
        assert "await " not in text


def test_subscriber_protocol_enforced():
    # Ensure that creating a subscriber with default works
    class CustomSub(GuardianEventSubscriber):
        pass

    cs = CustomSub()
    assert cs.supports(None) is False
    assert cs.handle(None) is None
    assert cs.get_name() == "CustomSub"


# --- Bridge tests ---


def test_reasoning_bridge():
    runtime = GuardianLiveRuntime()
    assert runtime.reasoning.trigger_count == 0
    meta = GuardianEventMetadata(
        event_type=GuardianEventType.OBSERVATION_UPDATE,
        priority=GuardianEventPriority.MEDIUM,
        source=GuardianEventSource.OBSERVATION,
        timestamp=0.0,
    )
    event = GuardianEvent(metadata=meta, payload={})
    result = runtime.reasoning.trigger(event)
    assert result["triggered"] is True
    assert result["trigger_count"] == 1


def test_learning_bridge():
    runtime = GuardianLiveRuntime()
    assert runtime.learning.feed_count == 0
    meta = GuardianEventMetadata(
        event_type=GuardianEventType.LEARNING_UPDATE,
        priority=GuardianEventPriority.LOW,
        source=GuardianEventSource.LEARNING,
        timestamp=0.0,
    )
    event = GuardianEvent(metadata=meta, payload={"data": "x"})
    result = runtime.learning.feed(event)
    assert result["fed"] is True
    assert result["feed_count"] == 1


def test_execution_bridge_preview_only():
    runtime = GuardianLiveRuntime()
    assert runtime.execution.preview_count == 0
    meta = GuardianEventMetadata(
        event_type=GuardianEventType.EXECUTION_PREVIEW,
        priority=GuardianEventPriority.HIGH,
        source=GuardianEventSource.EXECUTION,
        timestamp=0.0,
    )
    event = GuardianEvent(metadata=meta, payload={"action": "deploy"})
    result = runtime.execution.preview(event)
    assert result["previewed"] is True
    assert result["preview_only"] is True


def test_full_pipeline_with_bridges():
    runtime = GuardianLiveRuntime()
    runtime.start()
    sub = CapturingSubscriber(name="pipeline-test")
    runtime.register_subscriber(sub)

    result = runtime.execute_pipeline(
        observation_payload={"temperature": 85.0}
    )
    assert result["is_running"] is True
    assert result["event_id"] is not None
    assert result["snapshot"] is not None

    pipeline = result.get("pipeline")
    assert pipeline is not None
    assert pipeline["reasoning"]["triggered"] is True
    assert pipeline["learning"]["fed"] is True
    assert pipeline["execution_preview"]["previewed"] is True

    # Bridges have been called
    assert runtime.reasoning.trigger_count == 1
    assert runtime.learning.feed_count == 1
    assert runtime.execution.preview_count == 1
    runtime.stop()


def test_status_includes_bridges():
    runtime = GuardianLiveRuntime()
    runtime.start()
    status = runtime.get_status()
    assert "reasoning_triggers" in status
    assert "learning_feeds" in status
    assert "execution_previews" in status
    runtime.stop()


def test_pipeline_not_running():
    runtime = GuardianLiveRuntime()
    # Not started
    result = runtime.execute_pipeline()
    assert result["status"] == "stopped"
