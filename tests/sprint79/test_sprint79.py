import os, sys
import pytest
from dataclasses import FrozenInstanceError
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.operational_goal import GoalType, OperationalGoal
from sam.operational_brain.operational_candidate import OperationalCandidate
from sam.operational_brain.operational_builder import OperationalBuilder
from sam.operational_brain.operational_planner import OperationalPlanner, PlanEntry, PriorityTier
from sam.operational_brain.operational_planning import OperationalPlanning
from sam.operational_brain.operational_scheduler import OperationalScheduler
from sam.operational_brain.operational_plan_exporter import (
    OperationalPlan,
    PlanDocument,
    OperationalPlanExporter,
)
from sam.operational_brain.conversation_plan_export import ConversationPlanExport
from sam.operational_brain.dashboard_plan_export import DashboardPlanExport, PlanExportCard


# --- Helpers ---

def _ctx(env="normal", decisions=0, missions=None, source="manual", resources=2):
    return OperationalContext(
        context_id="pe_ctx", timestamp=300.0, source=source,
        environment=env, active_missions=missions or [],
        pending_decisions=decisions, pending_approvals=0, available_resources=resources,
    )


def _make_exporter():
    return OperationalPlanExporter()


# --- DTO frozen ---

def test_operational_plan_frozen():
    p = OperationalPlan(plan_id="p1", source="manual", entries=5, schedule_items=3, total_duration=30.0)
    with pytest.raises(FrozenInstanceError):
        p.entries = 99


def test_plan_document_frozen():
    d = PlanDocument(title="Doc1")
    with pytest.raises(FrozenInstanceError):
        d.title = "X"


def test_plan_export_card_frozen():
    c = PlanExportCard(title="C", value=1)
    with pytest.raises(FrozenInstanceError):
        c.title = "X"


# --- Exporter ---

def test_exporter_run_full_pipeline():
    exporter = _make_exporter()
    ctx = _ctx(env="busy", decisions=2, missions=["m1"])
    plan = exporter.run_full_pipeline(ctx)
    assert isinstance(plan, OperationalPlan)
    assert plan.entries >= 1
    assert plan.schedule_items >= 1
    assert plan.source == "manual"


def test_exporter_export_plan():
    exporter = _make_exporter()
    ctx = _ctx(env="busy", decisions=1)
    plan = exporter.run_full_pipeline(ctx)
    doc = exporter.export_plan(plan)
    assert isinstance(doc, PlanDocument)
    assert doc.title.startswith("Operational Plan:")
    assert isinstance(doc.entries, list)
    assert isinstance(doc.schedule, list)


def test_exporter_summary():
    exporter = _make_exporter()
    ctx = _ctx(env="busy", decisions=1)
    s = exporter.summary(ctx)
    assert "plan_id" in s
    assert "entries" in s
    assert "schedule_items" in s
    assert "duration" in s


def test_exporter_empty_context():
    exporter = _make_exporter()
    ctx = _ctx()  # normal, no decisions, no missions
    plan = exporter.run_full_pipeline(ctx)
    assert plan.entries >= 1  # idle fallback
    doc = exporter.export_plan(plan)
    assert len(doc.entries) >= 1


def test_exporter_emergency_context():
    exporter = _make_exporter()
    ctx = _ctx(env="emergency", decisions=3, resources=-1)
    plan = exporter.run_full_pipeline(ctx)
    assert plan.entries >= 1
    assert plan.schedule_items >= 1


def test_exporter_all_sources():
    exporter = _make_exporter()
    for src in ["manual", "inbox", "timer", "event"]:
        ctx = _ctx(source=src)
        plan = exporter.run_full_pipeline(ctx)
        assert plan.source == src


# --- ConversationPlanExport ---

def test_conversation_plan_export_query_count():
    exporter = _make_exporter()
    conv = ConversationPlanExport(exporter)
    assert conv.query_count == 6


def test_conversation_plan_export_summary():
    exporter = _make_exporter()
    conv = ConversationPlanExport(exporter)
    ctx = _ctx(env="busy", decisions=1)
    d = conv.query_plan_summary(ctx)
    assert "entries" in d
    assert "schedule_items" in d


def test_conversation_plan_export_details():
    exporter = _make_exporter()
    conv = ConversationPlanExport(exporter)
    ctx = _ctx(env="busy", decisions=1)
    d = conv.query_plan_details(ctx)
    assert "title" in d
    assert "entries" in d
    assert "schedule" in d


def test_conversation_plan_export_entries():
    exporter = _make_exporter()
    conv = ConversationPlanExport(exporter)
    ctx = _ctx(env="busy", decisions=1)
    entries = conv.query_entries_only(ctx)
    assert isinstance(entries, list)
    for e in entries:
        assert "entry_id" in e


def test_conversation_plan_export_schedule():
    exporter = _make_exporter()
    conv = ConversationPlanExport(exporter)
    ctx = _ctx(env="busy", decisions=1)
    sched = conv.query_schedule_only(ctx)
    assert isinstance(sched, list)
    for s in sched:
        assert "schedule_id" in s


def test_conversation_plan_export_last_plan_none():
    exporter = _make_exporter()
    conv = ConversationPlanExport(exporter)
    d = conv.query_last_plan()
    assert d == {"msg": "No plan generated yet"}


def test_conversation_plan_export_last_plan_after_run():
    exporter = _make_exporter()
    conv = ConversationPlanExport(exporter)
    ctx = _ctx()
    conv.query_plan_summary(ctx)
    d = conv.query_last_plan()
    assert "plan_id" in d


def test_conversation_plan_export_quick_source():
    exporter = _make_exporter()
    conv = ConversationPlanExport(exporter)
    d = conv.query_quick_summary_by_source("manual")
    assert "entries" in d


# --- DashboardPlanExport ---

def test_dashboard_plan_export_card_count():
    exporter = _make_exporter()
    dash = DashboardPlanExport(exporter)
    ctx = _ctx(env="busy", decisions=1)
    cards = dash.get_cards(ctx)
    assert len(cards) == dash.card_count == 5
    for card in cards:
        assert isinstance(card, PlanExportCard)


def test_dashboard_plan_export_card_types():
    exporter = _make_exporter()
    dash = DashboardPlanExport(exporter)
    ctx = _ctx(env="busy", decisions=1)
    types = [c.card_type for c in dash.get_cards(ctx)]
    assert "plan" in types
    assert "entries" in types
    assert "schedule" in types
    assert "duration" in types
    assert "source" in types


# --- Parametrized ---

@pytest.mark.parametrize("i", list(range(1, 26)))
def test_exporter_various_contexts(i):
    enums = ["normal", "busy", "idle", "emergency"]
    ctx = _ctx(env=enums[i % 4], decisions=i % 3, missions=[f"m{j}" for j in range(i % 4)])
    exporter = _make_exporter()
    plan = exporter.run_full_pipeline(ctx)
    assert plan.entries >= 1
    assert plan.schedule_items >= 1
    doc = exporter.export_plan(plan)
    assert len(doc.entries) == plan.entries
    assert len(doc.schedule) == plan.schedule_items


@pytest.mark.parametrize("source", ["manual", "inbox", "timer", "event", "webhook"])
def test_exporter_sources(source):
    ctx = _ctx(source=source)
    exporter = _make_exporter()
    s = exporter.summary(ctx)
    assert s["source"] == source


# --- Frozen edge cases ---

def test_export_document_with_data():
    exporter = _make_exporter()
    ctx = _ctx(env="busy", decisions=1)
    plan = exporter.run_full_pipeline(ctx)
    doc = exporter.export_plan(plan)
    assert doc.metadata["total_entries"] >= 1
    assert doc.metadata["schedule_items"] >= 1


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
    assert not bad, f"Found forbidden imports: {bad}"


def test_ast_parse_all():
    for path in _all_files():
        with open(path, 'r', encoding='utf-8') as fh:
            src = fh.read()
        ast.parse(src, filename=path)
