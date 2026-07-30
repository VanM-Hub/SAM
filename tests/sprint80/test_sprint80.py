import os, sys
import pytest
from dataclasses import FrozenInstanceError
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.operational_brain.operational_context import OperationalContext
from sam.operational_brain.readiness_checker import (
    ReadinessStatus,
    ReadinessCheck,
    ReadinessReport,
    ReadinessChecker,
)
from sam.operational_brain.conversation_readiness import ConversationReadiness
from sam.operational_brain.dashboard_readiness import DashboardReadiness, ReadinessCard


# --- Helpers ---

def _ctx(env="normal", resources=2, decisions=0, approvals=0, missions=None, constraints=None):
    return OperationalContext(
        context_id="r_ctx", timestamp=400.0, source="manual",
        environment=env, active_missions=missions or [],
        pending_decisions=decisions, pending_approvals=approvals,
        available_resources=resources,
        active_constraints=constraints or [],
    )


# --- DTO frozen ---

def test_readiness_check_frozen():
    c = ReadinessCheck(check_id="R01", name="Test", passed=True, score=1.0, status=ReadinessStatus.READY, message="ok")
    with pytest.raises(FrozenInstanceError):
        c.passed = False


def test_readiness_report_frozen():
    r = ReadinessReport(overall_score=1.0, overall_status=ReadinessStatus.READY, passed=2, total=2, summary="ok")
    with pytest.raises(FrozenInstanceError):
        r.passed = 99


def test_readiness_card_frozen():
    c = ReadinessCard(title="C", value=1)
    with pytest.raises(FrozenInstanceError):
        c.title = "X"


# --- ReadinessStatus enum ---

def test_readiness_status_members():
    names = [s.name for s in ReadinessStatus]
    assert names == ["READY", "DEGRADED", "BLOCKED", "MAINTENANCE", "UNKNOWN"]


# --- ReadinessChecker ---

def test_checker_categories():
    checker = ReadinessChecker()
    cats = checker.categories
    assert len(cats) == 8
    assert "resources" in cats
    assert "readiness" in cats


def test_checker_ready():
    checker = ReadinessChecker()
    ctx = _ctx()
    report = checker.check_all(ctx)
    assert report.overall_status == ReadinessStatus.READY
    assert report.passed == report.total
    assert report.overall_score >= 0.95


def test_checker_no_resources():
    checker = ReadinessChecker()
    ctx = _ctx(resources=0, decisions=2, approvals=3, env="busy")
    report = checker.check_all(ctx)
    assert report.overall_status in (ReadinessStatus.BLOCKED, ReadinessStatus.DEGRADED)
    assert report.passed < report.total


def test_checker_emergency_blocked():
    checker = ReadinessChecker()
    ctx = _ctx(env="emergency", resources=-1, decisions=5, approvals=5, constraints=["c1", "c2", "c3"])
    report = checker.check_all(ctx)
    for c in report.checks:
        if c.check_id in ("R01", "R03", "R04", "R07"):
            assert not c.passed, f"{c.check_id} should not pass in emergency"
    assert report.overall_score < 0.5


def test_checker_busy_but_ok():
    checker = ReadinessChecker()
    ctx = _ctx(env="busy", resources=2, decisions=1, approvals=1)
    report = checker.check_all(ctx)
    assert report.overall_status in (ReadinessStatus.READY, ReadinessStatus.DEGRADED)


def test_checker_many_constraints():
    checker = ReadinessChecker()
    ctx = _ctx(constraints=["c1", "c2", "c3"])
    report = checker.check_all(ctx)
    for c in report.checks:
        if c.check_id == "R04":
            assert not c.passed
            break


def test_checker_report_dict():
    checker = ReadinessChecker()
    ctx = _ctx()
    d = checker.report_dict(ctx)
    assert "overall_score" in d
    assert "overall_status" in d
    assert "checks" in d
    assert len(d["checks"]) == 8


def test_checker_idle_no_missions():
    checker = ReadinessChecker()
    ctx = _ctx(env="idle", resources=1, missions=[])
    report = checker.check_all(ctx)
    for c in report.checks:
        if c.check_id == "R05":
            assert c.status == ReadinessStatus.DEGRADED
            assert "No active missions" in c.message
            break


# --- ConversationReadiness ---

def test_conversation_readiness_count():
    conv = ConversationReadiness()
    assert conv.query_count == 5


def test_conversation_readiness_summary():
    conv = ConversationReadiness()
    ctx = _ctx()
    d = conv.query_readiness_summary(ctx)
    assert "overall_score" in d
    assert d["overall_status"] == "READY"


def test_conversation_readiness_detail():
    conv = ConversationReadiness()
    ctx = _ctx()
    lst = conv.query_readiness_detail(ctx)
    assert len(lst) == 8
    for item in lst:
        assert "check_id" in item
        assert "passed" in item


def test_conversation_readiness_failed():
    conv = ConversationReadiness()
    ctx = _ctx(resources=0, decisions=5, env="emergency")
    failed = conv.query_failed_checks(ctx)
    assert len(failed) >= 1
    for f in failed:
        assert "check_id" in f


def test_conversation_readiness_by_status():
    conv = ConversationReadiness()
    ctx = _ctx()
    ready = conv.query_by_status(ctx, "READY")
    assert len(ready) >= 1


def test_conversation_readiness_categories():
    conv = ConversationReadiness()
    cats = conv.query_categories()
    assert len(cats) == 8


# --- DashboardReadiness ---

def test_dashboard_readiness_card_count():
    dash = DashboardReadiness()
    ctx = _ctx()
    cards = dash.get_cards(ctx)
    assert len(cards) == dash.card_count == 5
    for card in cards:
        assert isinstance(card, ReadinessCard)


def test_dashboard_readiness_card_types():
    dash = DashboardReadiness()
    ctx = _ctx()
    types = [c.card_type for c in dash.get_cards(ctx)]
    assert "overall" in types
    assert "checks" in types
    assert "scores" in types
    assert "issues" in types
    assert "categories" in types


def test_dashboard_readiness_with_failures():
    dash = DashboardReadiness()
    ctx = _ctx(resources=0, env="emergency")
    cards = dash.get_cards(ctx)
    issues_card = [c for c in cards if c.card_type == "issues"][0]
    assert len(issues_card.value) >= 1


# --- Parametrized ---

@pytest.mark.parametrize("i", list(range(1, 26)))
def test_checker_various_scenarios(i):
    checker = ReadinessChecker()
    envs = ["normal", "busy", "idle", "emergency"]
    ctx = _ctx(
        env=envs[i % 4],
        resources=[-1, 0, 1, 2][i % 4],
        decisions=i % 4,
        approvals=i % 3,
        missions=[f"m{j}" for j in range(i % 3)],
        constraints=[f"c{j}" for j in range(i % 3)],
    )
    report = checker.check_all(ctx)
    assert 0.0 <= report.overall_score <= 1.0
    assert len(report.checks) == 8
    assert report.passed + (report.total - report.passed) == report.total
    for c in report.checks:
        assert 0.0 <= c.score <= 1.0


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
