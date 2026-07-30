import os, sys, pytest
from dataclasses import FrozenInstanceError
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.activation.activation_metrics import ActivationMetricsCollector, ActivationMetrics
from sam.activation.activation_monitor import ActivationMonitor, MonitorEvent
from sam.activation.activation_history import ActivationHistory, HistoryEntry
from sam.activation.activation_snapshot import ActivationSnapshotState
from sam.activation.activation_health import ActivationHealthChecker, ActivationHealthReport
from sam.activation.conversation_monitor import ConversationMonitor
from sam.activation.dashboard_monitor import DashboardMonitor, MonitorCard
from sam.activation.package_registry import PackageRegistry
from sam.activation.activation_package import ActivationPackage
from sam.activation.activation_strategy import ActivationStrategy
from dataclasses import FrozenInstanceError


# Helpers
def _pkg(strat="direct"):
    return ActivationPackage(f"pkg_{strat}", "plan", strat, "seq",
                             ["c1"], 1, 30.0, 0.95, "built")


def _reg():
    r = PackageRegistry()
    r.register(_pkg("direct"))
    r.register(_pkg("staged"))
    return r


# --- Frozen DTOs ---

def test_metrics_frozen():
    m = ActivationMetrics("m1", 2, 3, 0.5, 10.0)
    with pytest.raises(FrozenInstanceError):
        m.metrics_id = "x"


def test_event_frozen():
    e = MonitorEvent("e1", "built", "pkg1")
    with pytest.raises(FrozenInstanceError):
        e.event_id = "x"


def test_history_frozen():
    h = HistoryEntry("h1", "pkg1", "build")
    with pytest.raises(FrozenInstanceError):
        h.entry_id = "x"


def test_snapshot_frozen():
    s = ActivationSnapshotState("s1", 2, 3, 1)
    with pytest.raises(FrozenInstanceError):
        s.snapshot_id = "x"


def test_health_frozen():
    r = ActivationHealthReport(True, 2, 0.8, 3)
    with pytest.raises(FrozenInstanceError):
        r.healthy = False


def test_monitor_card_frozen():
    c = MonitorCard("t", "T")
    with pytest.raises(FrozenInstanceError):
        c.card_type = "x"


# --- ActivationMetricsCollector ---

def test_metrics_collector():
    coll = ActivationMetricsCollector()
    m = coll.collect(_reg().list())
    assert m.total_packages == 2
    assert m.total_candidates == 2
    assert m.avg_confidence == 0.95
    assert m.avg_duration == 30.0
    assert "direct" in m.strategy_counts


def test_metrics_collector_empty():
    coll = ActivationMetricsCollector()
    m = coll.collect([])
    assert m.total_packages == 0
    assert m.avg_confidence == 0.0


# --- ActivationMonitor ---

def test_monitor_record():
    m = ActivationMonitor()
    pkg = _pkg()
    e = m.record("built", pkg)
    assert e.event_type == "built"
    assert e.package_ref == pkg.package_id
    assert m.count_events() == 1


def test_monitor_list():
    m = ActivationMonitor()
    m.record("a", _pkg(), 1.0)
    m.record("b", _pkg(), 2.0)
    m.record("c", _pkg(), 3.0)
    events = m.list_events(2)
    assert len(events) == 2
    assert events[0].event_type == "b"


def test_monitor_by_type():
    m = ActivationMonitor()
    m.record("built", _pkg())
    m.record("validated", _pkg())
    m.record("built", _pkg())
    assert len(m.by_type("built")) == 2
    assert len(m.by_type("validated")) == 1


def test_monitor_clear():
    m = ActivationMonitor()
    m.record("built", _pkg())
    m.clear()
    assert m.count_events() == 0


# --- ActivationHistory ---

def test_history_record():
    h = ActivationHistory()
    pkg = _pkg()
    entry = h.record(pkg, "build")
    assert entry.action == "build"
    assert entry.package_id == pkg.package_id


def test_history_list():
    h = ActivationHistory()
    h.record(_pkg(), "a")
    h.record(_pkg(), "b")
    h.record(_pkg(), "c")
    assert len(h.list(2)) == 2
    assert h.count() == 3


def test_history_by_package():
    h = ActivationHistory()
    h.record(_pkg("direct"), "build")
    h.record(_pkg("staged"), "validate")
    assert len(h.by_package("pkg_direct")) == 1
    assert len(h.by_package("nonexistent")) == 0


def test_history_clear():
    h = ActivationHistory()
    h.record(_pkg(), "build")
    h.clear()
    assert h.count() == 0


# --- ActivationHealthChecker ---

def test_health_check_healthy():
    metrics = ActivationMetrics("m1", 2, 3, 0.8, 30.0)
    snap = ActivationSnapshotState("s1", 2, 5, 3, "active", metrics)
    checker = ActivationHealthChecker()
    r = checker.check(snap)
    assert r.healthy
    assert r.score >= 0.5


def test_health_check_unhealthy():
    snap = ActivationSnapshotState("s1", 0, 0, 0, "idle")
    checker = ActivationHealthChecker()
    r = checker.check(snap)
    assert not r.healthy


def test_health_check_low_confidence():
    metrics = ActivationMetrics("m1", 1, 1, 0.3, 10.0)
    snap = ActivationSnapshotState("s1", 1, 1, 1, "active", metrics)
    checker = ActivationHealthChecker()
    r = checker.check(snap)
    assert "Low confidence" in r.issues


# --- ConversationMonitor ---

def test_conversation_monitor_queries():
    reg = _reg()
    mon = ActivationMonitor()
    hist = ActivationHistory()
    conv = ConversationMonitor(reg, mon, hist)
    assert conv.query_count == 8


def test_conversation_metrics():
    reg = _reg()
    conv = ConversationMonitor(reg, ActivationMonitor(), ActivationHistory())
    m = conv.query_metrics(ActivationMetricsCollector())
    assert m["total_packages"] == 2


def test_conversation_health():
    reg = _reg()
    mon = ActivationMonitor()
    hist = ActivationHistory()
    pkg = _pkg()
    mon.record("built", pkg)
    hist.record(pkg, "build")
    conv = ConversationMonitor(reg, mon, hist)
    h = conv.query_health()
    assert "healthy" in h
    assert h["package_count"] == 2


# --- DashboardMonitor ---

def test_dashboard_monitor_cards():
    reg = _reg()
    mon = ActivationMonitor()
    hist = ActivationHistory()
    dash = DashboardMonitor(reg, mon, hist)
    assert dash.card_count == 5
    cards = dash.get_cards()
    assert len(cards) == 5
    types = [c.card_type for c in cards]
    assert "metrics" in types
    assert "events" in types
    assert "history" in types
    assert "snapshot" in types
    assert "health" in types


# --- Parametrized ---

@pytest.mark.parametrize("i", list(range(1, 41)))
def test_metrics_various(i):
    coll = ActivationMetricsCollector()
    cnt = i % 7
    pkgs = []
    for j in range(cnt):
        pkgs.append(ActivationPackage(
            f"pkg_{j}", "plan", f"str_{j % 3}", "seq",
            ["c1"], 1, 10.0 + j, 0.5 + (j * 0.1),
        ))
    m = coll.collect(pkgs)
    assert m.total_packages == cnt
    assert 0.0 <= m.avg_confidence <= 1.0


@pytest.mark.parametrize("i", list(range(1, 25)))
def test_monitor_various(i):
    mon = ActivationMonitor()
    for j in range(i % 15):
        mon.record(f"evt_type_{j % 3}", _pkg(), j * 100.0)
    assert mon.count_events() == i % 15
    events = mon.list_events(5)
    assert len(events) <= 5


@pytest.mark.parametrize("i", list(range(1, 25)))
def test_history_various(i):
    h = ActivationHistory()
    for j in range(i % 12):
        h.record(ActivationPackage(f"pkg_{j}", "plan"), f"act_{j % 4}", j * 100.0)
    assert h.count() == i % 12


@pytest.mark.parametrize("i", list(range(1, 30)))
def test_health_various(i):
    has_pkg = i % 2 == 0
    has_event = i % 3 == 0
    has_hist = i % 4 == 0
    conf = min(0.9, max(0.1, i / 10))
    metrics = ActivationMetrics("m", 1 if has_pkg else 0, 0, conf, 10.0)
    snap = ActivationSnapshotState(
        "s", 1 if has_pkg else 0, 1 if has_event else 0,
        1 if has_hist else 0, "active", metrics,
    )
    checker = ActivationHealthChecker()
    r = checker.check(snap)
    assert r.score >= 0.0


# --- Forbidden imports & AST ---

FORBIDDEN = [
    'sam.guardian', 'sam.approval', 'sam.execution',
    'sam.storage', 'sam.domain', 'sam.repository',
    'sam.conversation', 'sam.operational_brain',
    'thread', 'threading', 'asyncio', 'subprocess', 'requests', 'socket', 'network'
]


def _all_files():
    base = os.path.join(os.path.dirname(__file__), "..", "src", "sam", "activation")
    if not os.path.isdir(base):
        return
    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith('.py'):
                yield os.path.join(root, f)


def test_no_forbidden_imports():
    bad = []
    for path in _all_files():
        with open(path, 'r', encoding='utf-8') as fh:
            tree = ast.parse(fh.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    for f in FORBIDDEN:
                        if f in n.name:
                            bad.append((path, n.name))
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ''
                for f in FORBIDDEN:
                    if f in mod:
                        bad.append((path, mod))
    assert not bad, f"Forbidden: {bad}"


def test_ast_parse():
    for path in _all_files():
        with open(path, 'r', encoding='utf-8') as fh:
            ast.parse(fh.read(), filename=path)
