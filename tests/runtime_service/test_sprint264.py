"""Sprint 264 - Runtime Lifecycle.

Program D - Runtime Services & Deployment.
Created -> Initializing -> Ready -> Running -> Stopping -> Stopped | Failed
"""
from __future__ import annotations
import pytest

from sam.runtime_service.lifecycle import STATES
from sam.runtime_service.lifecycle.state import LifecycleState
from sam.runtime_service.lifecycle.transition import LifecycleTransition
from sam.runtime_service.lifecycle.validator import LifecycleValidator
from sam.runtime_service.lifecycle.history import LifecycleHistory
from sam.runtime_service.lifecycle.runtime import LifecycleRuntime


def test_states_present():
    for s in ("created", "initializing", "ready", "running",
              "stopping", "stopped", "failed"):
        assert s in STATES


def test_state_invalid_rejected():
    with pytest.raises(ValueError):
        LifecycleState(name="bogus")


def test_state_frozen():
    s = LifecycleState(name="ready")
    with pytest.raises(Exception):
        s.name = "running"
    assert s.as_dict()["name"] == "ready"


def test_state_factories():
    assert LifecycleState.created().name == "created"
    assert LifecycleState.ready().name == "ready"
    assert LifecycleState.failed().name == "failed"


def test_transition_valid():
    t = LifecycleTransition(source=LifecycleState.ready(),
                            target=LifecycleState.running())
    assert t.is_valid() is True


def test_transition_invalid_same():
    t = LifecycleTransition(source=LifecycleState.ready(),
                            target=LifecycleState.ready())
    assert t.is_valid() is False


def test_transition_illegal_skip():
    # created -> running tidak boleh
    t = LifecycleTransition(source=LifecycleState.created(),
                            target=LifecycleState.running())
    assert t.is_valid() is False


def test_transition_full_flow():
    flow = ["created", "initializing", "ready", "running",
            "stopping", "stopped"]
    for i in range(len(flow) - 1):
        assert LifecycleTransition(
            source=LifecycleState(name=flow[i]),
            target=LifecycleState(name=flow[i + 1]),
        ).is_valid()


def test_validator_can_transition():
    v = LifecycleValidator()
    assert v.can_transition(LifecycleState.running(),
                            LifecycleState.stopping()) is True
    assert v.can_transition(LifecycleState.stopped(),
                            LifecycleState.running()) is False


def test_validator_assert():
    v = LifecycleValidator()
    v.assert_valid(LifecycleState.initializing(), LifecycleState.ready())
    with pytest.raises(ValueError):
        v.assert_valid(LifecycleState.ready(), LifecycleState.initializing())


def test_validator_next_states():
    v = LifecycleValidator()
    nxt = v.next_states(LifecycleState.ready())
    assert "running" in nxt
    assert v.next_states(LifecycleState.stopped()) == []


def test_history_append_count():
    h = LifecycleHistory()
    assert h.count() == 0
    h.append(LifecycleTransition(LifecycleState.created(), LifecycleState.initializing()))
    assert h.count() == 1


def test_history_last():
    h = LifecycleHistory()
    assert h.last() == "created"
    h.append(LifecycleTransition(LifecycleState.created(), LifecycleState.initializing()))
    assert h.last() == "initializing"


def test_lifecycle_runtime_initial():
    lr = LifecycleRuntime()
    assert lr.status == "created"


def test_lifecycle_runtime_finished():
    lr = LifecycleRuntime()
    lr.transition(LifecycleState.initializing())
    lr.transition(LifecycleState.ready())
    lr.transition(LifecycleState.running())
    lr.transition(LifecycleState.stopping())
    lr.transition(LifecycleState.stopped())
    assert lr.status == "stopped"


def test_lifecycle_runtime_invalid_raises():
    lr = LifecycleRuntime()
    with pytest.raises(ValueError):
        lr.transition(LifecycleState.running())  # skip, tidak valid


def test_lifecycle_runtime_history_records():
    lr = LifecycleRuntime()
    lr.transition(LifecycleState.initializing())
    lr.transition(LifecycleState.ready())
    hist = lr.history()
    assert hist[0] == {"source": "created", "target": "initializing"}
    assert hist[1] == {"source": "initializing", "target": "ready"}


def test_lifecycle_runtime_failed_from_ready():
    lr = LifecycleRuntime()
    lr.transition(LifecycleState.initializing())
    lr.transition(LifecycleState.ready())
    lr.transition(LifecycleState.failed())
    assert lr.status == "failed"


def test_lifecycle_runtime_next_states():
    lr = LifecycleRuntime(LifecycleState.ready())
    assert set(lr.next_states()) == {"running", "stopped", "failed"}
