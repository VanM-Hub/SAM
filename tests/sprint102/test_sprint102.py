"""Sprint 102 — Runtime State Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.runtime_kernel.runtime_state import (
    RuntimeState, StateMachine, StateSnapshot,
    StateHistoryEntry, StateValidation,
)
from sam.runtime_kernel.state_machine import StateMachineEngine
from sam.runtime_kernel.state_snapshot import SnapshotEngine
from sam.runtime_kernel.state_history import StateHistory
from sam.runtime_kernel.state_validator import StateValidator
from sam.runtime_kernel.conversation_state import ConversationState, DashboardState
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. DTO Tests
# ============================================================

class TestRuntimeState:
    def test_create(self):
        s = RuntimeState("s1", "ready", "booting")
        assert s.state == "ready"

    def test_immutable(self):
        s = RuntimeState("s", "initial")
        with pytest.raises(FrozenInstanceError):
            s.state = "ready"


class TestStateMachine:
    def test_create(self):
        m = StateMachine("m1", {"init": "boot"}, "boot")
        assert m.current_state == "boot"

    def test_immutable(self):
        m = StateMachine("m")
        with pytest.raises(FrozenInstanceError):
            m.current_state = "ready"


class TestStateSnapshot:
    def test_create(self):
        s = StateSnapshot("s1", 100.0, "ready", {"guardian": "active"})
        assert s.components["guardian"] == "active"

    def test_immutable(self):
        s = StateSnapshot("s", 0.0, "init")
        with pytest.raises(FrozenInstanceError):
            s.state = "ready"


class TestStateHistoryEntry:
    def test_create(self):
        e = StateHistoryEntry("e1", "ready", "boot→ready", 200.0)
        assert e.transition == "boot→ready"

    def test_immutable(self):
        e = StateHistoryEntry("e", "init")
        with pytest.raises(FrozenInstanceError):
            e.state = "ready"


class TestStateValidation:
    def test_valid(self):
        v = StateValidation("v1", True)
        assert v.valid

    def test_invalid(self):
        v = StateValidation("v1", False, ["error1"])
        assert not v.valid

    def test_immutable(self):
        v = StateValidation("v")
        with pytest.raises(FrozenInstanceError):
            v.valid = False


# ============================================================
# 2. Engine Tests
# ============================================================

class TestStateMachineEngine:
    def test_create(self):
        e = StateMachineEngine()
        m = e.create("m1")
        assert m.current_state == "initial"

    def test_transition_valid(self):
        e = StateMachineEngine()
        e.create("m1")
        m = e.transition("m1", "booting")
        assert m is not None
        assert m.current_state == "booting"

    def test_transition_invalid(self):
        e = StateMachineEngine()
        e.create("m1")
        m = e.transition("m1", "active")  # can't go from initial to active
        assert m is None

    def test_transition_missing_machine(self):
        e = StateMachineEngine()
        m = e.transition("bogus", "ready")
        assert m is None

    def test_can_transition(self):
        e = StateMachineEngine()
        e.create("m1")
        assert e.can_transition("m1", "booting")
        assert not e.can_transition("m1", "active")

    def test_full_path(self):
        e = StateMachineEngine()
        e.create("m1")
        for state in ["booting", "ready", "active", "suspended", "ready", "shutdown"]:
            m = e.transition("m1", state)
            assert m is not None, f"Failed transition to {state}"
            assert m.current_state == state

    def test_get(self):
        e = StateMachineEngine()
        e.create("m1")
        assert e.get("m1") is not None
        assert e.get("bogus") is None


class TestSnapshotEngine:
    def test_create(self):
        e = SnapshotEngine()
        s = e.create("s1", 1.0, "ready", {"g": "active"})
        assert s.state == "ready"
        assert e.count() == 1

    def test_get(self):
        e = SnapshotEngine()
        e.create("s1", 1.0, "ready")
        assert e.get("s1") is not None
        assert e.get("bogus") is None

    def test_list_all(self):
        e = SnapshotEngine()
        e.create("s1", 1.0, "ready")
        e.create("s2", 2.0, "active")
        assert len(e.list_all()) == 2


class TestStateHistory:
    def test_record(self):
        h = StateHistory()
        e = h.record("e1", "ready", "boot→ready", 100.0)
        assert h.count() == 1
        assert e.state == "ready"

    def test_get_all(self):
        h = StateHistory()
        h.record("e1", "ready")
        assert len(h.get_all()) == 1

    def test_last_state(self):
        h = StateHistory()
        h.record("e1", "ready")
        h.record("e2", "active")
        assert h.last_state() == "active"

    def test_empty_last(self):
        h = StateHistory()
        assert h.last_state() == ""

    def test_filter_by_state(self):
        h = StateHistory()
        h.record("e1", "ready")
        h.record("e2", "active")
        h.record("e3", "ready")
        assert len(h.filter_by_state("ready")) == 2
        assert len(h.filter_by_state("active")) == 1


class TestStateValidator:
    def test_valid(self):
        v = StateValidator()
        r = v.validate("v1", "ready")
        assert r.valid

    def test_invalid(self):
        v = StateValidator()
        r = v.validate("v1", "bogus")
        assert not r.valid
        assert len(r.errors) == 1

    def test_is_valid(self):
        v = StateValidator()
        assert v.is_valid("ready")
        assert not v.is_valid("bogus")


# ============================================================
# 3. Conversation State
# ============================================================

class TestConversationState:
    def test_queries(self):
        cs = ConversationState(StateMachineEngine(), SnapshotEngine(),
                               StateHistory(), StateValidator())
        assert cs.get_machine_engine() is not None
        assert cs.get_snapshot_engine() is not None
        assert cs.get_history() is not None
        assert cs.get_validator() is not None
        layers = cs.describe_layers()
        assert len(layers) == 4
        assert cs.count_layers() == 4
        states = cs.get_valid_states()
        assert len(states) == 7
        assert cs.count_states() == 7


# ============================================================
# 4. Dashboard State
# ============================================================

class TestDashboardState:
    def test_cards(self):
        ds = DashboardState(StateMachineEngine(), SnapshotEngine(), StateHistory())
        for card in [ds.engine_card(), ds.snapshot_card(), ds.history_card(),
                     ds.validation_card(), ds.summary_card()]:
            assert card.status == "ready"
            assert len(card.metrics) >= 1

    def test_all_frozen(self):
        ds = DashboardState(StateMachineEngine(), SnapshotEngine(), StateHistory())
        for card in [ds.engine_card(), ds.snapshot_card(), ds.history_card(),
                     ds.validation_card(), ds.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        RuntimeState("s", "init"),
        StateMachine("m"),
        StateSnapshot("s", 0.0, "init"),
        StateHistoryEntry("e", "init"),
        StateValidation("v"),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(obj, list(vars(obj).keys())[0], "x")


# ============================================================
# 6. Forbidden Imports
# ============================================================

class TestForbiddenImports:
    def test_0_forbidden_imports(self):
        import ast, pathlib
        forbidden = [
            "asyncio", "threading", "multiprocessing", "socket",
            "http", "urllib", "requests", "aiohttp",
            "subprocess", "os.system", "shutil",
            "sqlite3", "mysql", "postgresql",
            "redis", "celery", "rabbitmq", "kafka",
        ]
        src_dir = pathlib.Path("src/sam/runtime_kernel")
        if not src_dir.exists():
            pytest.skip("runtime_kernel dir not found")
        errors = []
        for f in sorted(src_dir.glob("*.py")):
            tree = ast.parse(f.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name.split(".")[0]
                        if name in forbidden:
                            errors.append(f"{f.name}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        name = node.module.split(".")[0]
                        if name in forbidden:
                            errors.append(f"{f.name}: from {node.module}")
        assert not errors, f"Forbidden imports found: {errors}"


# ============================================================
# 7. Parametrized Tests
# ============================================================

@pytest.mark.parametrize("i", list(range(1, 36)))
def test_fsm_parametrized(i):
    e = StateMachineEngine()
    e.create(f"m{i}")
    if i % 2 == 0:
        m = e.transition(f"m{i}", "booting")
        assert m is not None


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_snapshot_parametrized(i):
    e = SnapshotEngine()
    s = e.create(f"s{i}", float(i), "ready" if i % 2 == 0 else "active",
                 {f"comp{j}": "ok" for j in range(i % 5)})
    assert len(s.components) == i % 5


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_history_parametrized(i):
    h = StateHistory()
    for j in range(i % 7 + 1):
        states = ["initial", "booting", "ready", "active", "suspended", "shutdown"]
        h.record(f"e{j}", states[j % len(states)])
    assert h.count() == i % 7 + 1


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_validator_parametrized(i):
    v = StateValidator()
    state = "ready" if i % 2 == 0 else "bogus"
    r = v.validate(f"v{i}", state)
    assert r.valid == (state != "bogus")


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_parametrized(i):
    cs = ConversationState(StateMachineEngine(), SnapshotEngine(),
                           StateHistory(), StateValidator())
    assert cs.count_states() == 7


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_parametrized(i):
    ds = DashboardState(StateMachineEngine(), SnapshotEngine(), StateHistory())
    c = ds.engine_card()
    assert c.status == "ready"
