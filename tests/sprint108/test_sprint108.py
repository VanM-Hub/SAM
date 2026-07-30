"""Sprint 108 — Runtime Event Bus Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.runtime_kernel.runtime_event import (
    RuntimeEvent, EventSubscription, EventLog, EventDispatch,
)
from sam.runtime_kernel.event_bus import EventBus
from sam.runtime_kernel.event_dispatcher import EventDispatcher
from sam.runtime_kernel.event_logger import EventLogger
from sam.runtime_kernel.event_filter import EventFilter
from sam.runtime_kernel.conversation_event import ConversationEvent, DashboardEvent
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. DTO Tests
# ============================================================

class TestRuntimeEvent:
    def test_create(self):
        e = RuntimeEvent("e1", "boot", "kernel", {"phase": "init"})
        assert e.event_type == "boot"

    def test_immutable(self):
        e = RuntimeEvent("e", "type")
        with pytest.raises(FrozenInstanceError):
            e.event_type = "new"


class TestEventSubscription:
    def test_create(self):
        s = EventSubscription("s1", "boot", "kernel_boot", True)
        assert s.active

    def test_immutable(self):
        s = EventSubscription("s", "t")
        with pytest.raises(FrozenInstanceError):
            s.active = False


class TestEventLog:
    def test_create(self):
        l = EventLog("l1", count=3)
        assert l.count == 3

    def test_immutable(self):
        l = EventLog("l")
        with pytest.raises(FrozenInstanceError):
            l.count = 5


class TestEventDispatch:
    def test_handled(self):
        d = EventDispatch("d1", "e1", True, ["handler1"])
        assert d.handled

    def test_immutable(self):
        d = EventDispatch("d", "e")
        with pytest.raises(FrozenInstanceError):
            d.handled = True


# ============================================================
# 2. Engine Tests
# ============================================================

class TestEventBus:
    def test_subscribe(self):
        b = EventBus()
        b.subscribe(EventSubscription("s1", "boot", "handler"))
        assert b.count_subs() == 1

    def test_unsubscribe(self):
        b = EventBus()
        b.subscribe(EventSubscription("s1", "boot", "handler"))
        assert b.unsubscribe("s1")
        assert b.count_subs() == 0

    def test_unsubscribe_missing(self):
        b = EventBus()
        assert not b.unsubscribe("bogus")

    def test_publish(self):
        b = EventBus()
        b.subscribe(EventSubscription("s1", "boot", "handler1"))
        d = b.publish(RuntimeEvent("e1", "boot", "kernel"))
        assert d.handled
        assert len(d.handlers) == 1
        assert b.count_events() == 1

    def test_publish_no_sub(self):
        b = EventBus()
        d = b.publish(RuntimeEvent("e1", "boot", "kernel"))
        assert not d.handled

    def test_get_subscription(self):
        b = EventBus()
        b.subscribe(EventSubscription("s1", "boot", "handler"))
        assert b.get_subscription("s1") is not None
        assert b.get_subscription("bogus") is None

    def test_find_by_type(self):
        b = EventBus()
        b.publish(RuntimeEvent("e1", "boot", "k"))
        b.publish(RuntimeEvent("e2", "shutdown", "k"))
        b.publish(RuntimeEvent("e3", "boot", "d"))
        assert len(b.find_by_type("boot")) == 2


class TestEventDispatcher:
    def test_dispatch_to(self):
        d = EventDispatcher()
        e = RuntimeEvent("e1", "boot", "kernel")
        result = d.dispatch_to(e, ["h1", "h2"])
        assert result.handled
        assert len(result.handlers) == 2

    def test_dispatch_to_empty(self):
        d = EventDispatcher()
        e = RuntimeEvent("e1", "boot", "kernel")
        result = d.dispatch_to(e, [])
        assert not result.handled

    def test_batch_dispatch(self):
        d = EventDispatcher()
        events = [RuntimeEvent("e1", "boot", "k"), RuntimeEvent("e2", "boot", "d")]
        subs = [EventSubscription("s1", "boot", "h1", True)]
        results = d.batch_dispatch(events, subs)
        assert len(results) == 2
        assert results[0].handled


class TestEventLogger:
    def test_log(self):
        l = EventLogger()
        l.log(RuntimeEvent("e1", "boot", "kernel"))
        assert l.count() == 1

    def test_get(self):
        l = EventLogger()
        l.log(RuntimeEvent("e1", "boot", "kernel"))
        assert l.get("e1") is not None
        assert l.get("bogus") is None

    def test_find_by_source(self):
        l = EventLogger()
        l.log(RuntimeEvent("e1", "boot", "kernel"))
        l.log(RuntimeEvent("e2", "boot", "decision"))
        assert len(l.find_by_source("kernel")) == 1

    def test_list_all(self):
        l = EventLogger()
        l.log(RuntimeEvent("e1", "boot", "kernel"))
        assert len(l.list_all()) == 1


class TestEventFilter:
    def test_filter_by_type(self):
        f = EventFilter()
        events = [
            RuntimeEvent("e1", "boot", "k"),
            RuntimeEvent("e2", "shutdown", "k"),
            RuntimeEvent("e3", "boot", "d"),
        ]
        assert len(f.filter_by_type(events, "boot")) == 2

    def test_filter_by_source(self):
        f = EventFilter()
        events = [
            RuntimeEvent("e1", "boot", "kernel"),
            RuntimeEvent("e2", "boot", "decision"),
        ]
        assert len(f.filter_by_source(events, "kernel")) == 1

    def test_filter_recent(self):
        f = EventFilter()
        events = [RuntimeEvent(f"e{i}", "boot", "k") for i in range(10)]
        assert len(f.filter_recent(events, 3)) == 3

    def test_filter_recent_all(self):
        f = EventFilter()
        events = [RuntimeEvent(f"e{i}", "boot", "k") for i in range(3)]
        assert len(f.filter_recent(events, 10)) == 3


# ============================================================
# 3. Conversation Event
# ============================================================

class TestConversationEvent:
    def test_queries(self):
        ce = ConversationEvent(EventBus(), EventDispatcher(),
                               EventLogger(), EventFilter())
        assert ce.get_bus() is not None
        assert ce.get_dispatcher() is not None
        assert ce.get_logger() is not None
        assert ce.get_filter() is not None
        layers = ce.describe_layers()
        assert len(layers) == 4
        assert ce.count_layers() == 4
        assert ce.get_sub_count() == 0
        assert ce.get_event_count() == 0


# ============================================================
# 4. Dashboard Event
# ============================================================

class TestDashboardEvent:
    def test_cards(self):
        de = DashboardEvent(EventBus(), EventLogger())
        for card in [de.engine_card(), de.subscription_card(), de.logger_card(),
                     de.filter_card(), de.summary_card()]:
            assert card.status == "ready"
            assert len(card.metrics) >= 1

    def test_all_frozen(self):
        de = DashboardEvent(EventBus(), EventLogger())
        for card in [de.engine_card(), de.subscription_card(), de.logger_card(),
                     de.filter_card(), de.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [
        RuntimeEvent("e", "t"),
        EventSubscription("s", "t"),
        EventLog("l"),
        EventDispatch("d", "e"),
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
# 7. Parametrized
# ============================================================

@pytest.mark.parametrize("i", list(range(1, 31)))
def test_bus_parametrized(i):
    b = EventBus()
    types = ["boot", "state", "shutdown", "error"]
    b.subscribe(EventSubscription(f"s{i}", types[i % 4], f"handler{i}"))
    e = b.publish(RuntimeEvent(f"e{i}", types[i % 4], "kernel"))
    assert e.handled
    assert b.count_subs() == 1


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_dispatch_parametrized(i):
    d = EventDispatcher()
    e = RuntimeEvent(f"e{i}", "boot", "kernel")
    handlers = [f"h{j}" for j in range(i % 5)]
    result = d.dispatch_to(e, handlers)
    assert result.handled == (len(handlers) > 0)


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_logger_parametrized(i):
    l = EventLogger()
    l.log(RuntimeEvent(f"e{i}", "boot", f"source{i % 3}"))
    assert l.count() == 1


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_filter_parametrized(i):
    f = EventFilter()
    events = [RuntimeEvent(f"e{j}", "boot" if j % 2 == 0 else "shutdown", "k")
              for j in range(i % 8 + 1)]
    filtered = f.filter_by_type(events, "boot")
    assert len(filtered) == sum(1 for e in events if e.event_type == "boot")


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_parametrized(i):
    ce = ConversationEvent(EventBus(), EventDispatcher(),
                           EventLogger(), EventFilter())
    assert ce.count_layers() == 4


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_parametrized(i):
    de = DashboardEvent(EventBus(), EventLogger())
    c = de.engine_card()
    assert c.status == "ready"
