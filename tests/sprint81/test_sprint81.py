import os, sys
import pytest
from dataclasses import FrozenInstanceError
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_planning import OperationalPlanning
from sam.operational_brain.operational_scheduler import OperationalScheduler
from sam.operational_brain.operational_metrics import OperationalMetrics, MetricsCollector
from sam.operational_brain.operational_monitor import CycleSnapshot, OperationalMonitor
from sam.operational_brain.health_aggregator import HealthReport, HealthAggregator
from sam.operational_brain.conversation_monitor import ConversationMonitor


# --- Helpers ---

def _ctx(env="normal", resources=2, decisions=0, missions=None):
    return OperationalContext(
        context_id="ms_ctx", timestamp=500.0, source="manual",
        environment=env, active_missions=missions or [],
        pending_decisions=decisions, pending_approvals=0, available_resources=resources,
    )


def _run_pipeline(env="busy", decisions=1):
    ctx = _ctx(env=env, decisions=decisions)
    planning = OperationalPlanning()
    scheduler = OperationalScheduler()
    plan = planning.run(ctx)
    scheduler.schedule_from_plan(plan, ctx)
    return planning, scheduler, ctx


# --- DTO frozen ---

def test_operational_metrics_frozen():
    m = OperationalMetrics(total_candidates_generated=5)
    with pytest.raises(FrozenInstanceError):
        m.total_candidates_generated = 99


def test_cycle_snapshot_frozen():
    s = CycleSnapshot(cycle_id="c1")
    with pytest.raises(FrozenInstanceError):
        s.cycle_id = "x"


def test_health_report_frozen():
    r = HealthReport(score=0.8, status="healthy", readiness=None, metrics=None)
    with pytest.raises(FrozenInstanceError):
        r.score = 0.5


# --- MetricsCollector ---

def test_metrics_collector_empty():
    planning = OperationalPlanning()
    scheduler = OperationalScheduler()
    collector = MetricsCollector()
    metrics = collector.collect(planning, scheduler)
    assert isinstance(metrics, OperationalMetrics)
    assert metrics.total_candidates_generated == 0


def test_metrics_collector_with_data():
    planning, scheduler, _ = _run_pipeline()
    collector = MetricsCollector()
    metrics = collector.collect(planning, scheduler)
    assert metrics.total_candidates_generated >= 1
    assert 0.0 <= metrics.avg_plan_score <= 1.0
    assert 0.0 <= metrics.avg_priority_score <= 1.0
    assert metrics.avg_schedule_position >= 0
    assert isinstance(metrics.tier_distribution, dict)


# --- HealthAggregator ---

def test_health_aggregator_ready():
    agg = HealthAggregator()
    ctx = _ctx()
    report = agg.assess(ctx)
    assert isinstance(report, HealthReport)
    assert report.score >= 0.6
    assert report.status in ("healthy", "degraded")


def test_health_aggregator_blocked():
    agg = HealthAggregator()
    ctx = _ctx(env="emergency", resources=-1, decisions=5)
    report = agg.assess(ctx)
    assert report.status == "blocked" or report.score < 0.6


def test_health_aggregator_dict():
    agg = HealthAggregator()
    ctx = _ctx()
    d = agg.report_dict(ctx)
    assert "health_score" in d
    assert "health_status" in d
    assert "readiness" in d
    assert "metrics" in d


# --- OperationalMonitor ---

def test_monitor_initial_state():
    mon = OperationalMonitor()
    assert mon.cycle_count == 0
    assert mon.last_snapshot() is None


def test_monitor_run_cycle():
    mon = OperationalMonitor()
    ctx = _ctx()
    snap = mon.run_cycle(ctx)
    assert isinstance(snap, CycleSnapshot)
    assert "cycle" in snap.cycle_id
    assert snap.plan_entries >= 1
    assert snap.schedule_items >= 1


def test_monitor_multiple_cycles():
    mon = OperationalMonitor()
    for i in range(3):
        ctx = _ctx(env=["normal", "busy", "emergency"][i], resources=i)
        mon.run_cycle(ctx)
    assert mon.cycle_count == 3
    assert len(mon.cycles) == 3


def test_monitor_context_diff():
    mon = OperationalMonitor()
    ctx1 = _ctx(env="normal", resources=2)
    mon.run_cycle(ctx1)
    ctx2 = _ctx(env="busy", resources=1, decisions=2)
    snap = mon.run_cycle(ctx2)
    assert snap.context_diff  # should have changes
    assert "environment" in snap.context_diff or "available_resources" in snap.context_diff or "pending_decisions" in snap.context_diff


def test_monitor_clear():
    mon = OperationalMonitor()
    mon.run_cycle(_ctx())
    mon.run_cycle(_ctx())
    mon.clear()
    assert mon.cycle_count == 0
    assert mon.last_snapshot() is None


# --- ConversationMonitor ---

def test_conversation_monitor_count():
    mon = OperationalMonitor()
    conv = ConversationMonitor(mon)
    assert conv.query_count == 5


def test_conversation_monitor_no_cycles():
    mon = OperationalMonitor()
    conv = ConversationMonitor(mon)
    assert conv.query_cycle_count() == 0
    snap = conv.query_last_snapshot()
    assert snap == {"msg": "No cycles yet"}


def test_conversation_monitor_run_and_query():
    mon = OperationalMonitor()
    conv = ConversationMonitor(mon)
    ctx = _ctx()
    result = conv.query_run_cycle(ctx)
    assert "cycle_id" in result
    assert result["plan_entries"] >= 1
    assert conv.query_cycle_count() == 1


def test_conversation_monitor_history():
    mon = OperationalMonitor()
    conv = ConversationMonitor(mon)
    conv.query_run_cycle(_ctx(env="normal"))
    conv.query_run_cycle(_ctx(env="busy"))
    history = conv.query_cycle_history()
    assert len(history) == 2
    for h in history:
        assert "cycle_id" in h


def test_conversation_monitor_recent_changes():
    mon = OperationalMonitor()
    conv = ConversationMonitor(mon)
    ctx1 = _ctx(env="normal")
    conv.query_run_cycle(ctx1)
    ctx2 = _ctx(env="emergency", resources=0, decisions=3)
    conv.query_run_cycle(ctx2)
    changes = conv.query_recent_changes()
    assert len(changes) >= 1


# --- Parametrized ---

@pytest.mark.parametrize("i", list(range(1, 21)))
def test_metrics_various_pipelines(i):
    envs = ["normal", "busy", "idle", "emergency"]
    ctx = _ctx(env=envs[i % 4], resources=[-1, 0, 1, 2][i % 4], decisions=i % 3)
    planning = OperationalPlanning()
    scheduler = OperationalScheduler()
    planning.run(ctx)
    scheduler.schedule_from_plan(planning.last_plan, ctx)
    collector = MetricsCollector()
    metrics = collector.collect(planning, scheduler)
    assert 0.0 <= metrics.avg_plan_score <= 1.0
    assert 0.0 <= metrics.avg_priority_score <= 1.0


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_health_various_contexts(i):
    agg = HealthAggregator()
    ctx = _ctx(
        env=["normal", "busy", "idle", "emergency"][i % 4],
        resources=[-1, 0, 1][i % 3],
        decisions=i % 4,
    )
    report = agg.assess(ctx)
    assert 0.0 <= report.score <= 1.0
    assert report.status in ("healthy", "degraded", "critical", "blocked")


# --- Forbidden imports ---

FORBIDDEN = [
    'sam.guardian', 'sam.approval', 'sam.execution', 'sam.conversation', 'sam.storage', 'sam.domain', 'sam.repository',
    'thread', 'threading', 'asyncio', 'subprocess', 'requests', 'socket', 'network'
]


def _all_files():
    base = os.path.join(os.path.dirname(__file__), "..", "src", "sam", "operational_brain")
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
    assert not bad


def test_ast_parse_all():
    for path in _all_files():
        with open(path, 'r', encoding='utf-8') as fh:
            src = fh.read()
        ast.parse(src, filename=path)
