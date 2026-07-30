import os, sys, pytest
from dataclasses import FrozenInstanceError
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.activation.activation_runtime import ActivationRuntimeEngine, RuntimeStatus
from sam.activation.activation_pipeline import ActivationPipeline
from sam.activation.activation_coordinator import ActivationCoordinator
from sam.activation.activation_runtime_report import RuntimeReport, RuntimeReportBuilder
from sam.activation.activation_runtime_status import ActivationRuntimeStatus, ActivationRuntimeStatusBuilder
from sam.activation.conversation_runtime import ConversationRuntime
from sam.activation.dashboard_runtime import DashboardRuntime, RuntimeCard
from sam.activation.activation_context import ActivationContext
from sam.activation.activation_request import ActivationRequest
from sam.activation.activation_candidate import ActivationCandidate
from sam.activation.activation_metrics import ActivationMetricsCollector, ActivationMetrics
from sam.activation.activation_snapshot import ActivationSnapshotState
from sam.activation.activation_health import ActivationHealthChecker, ActivationHealthReport


# Helpers
def _ctx():
    return ActivationContext("ctx_rt", 1000.0, "plan_rt", "normal", 3, 2,
                             "dec_rt", "app_rt")


def _req():
    return ActivationRequest("req_rt", "plan_rt", 1000.0, "system", "normal")


# --- Frozen DTOs ---

def test_runtime_status_frozen():
    s = RuntimeStatus(True, "building", 2, 100.0, "running")
    with pytest.raises(FrozenInstanceError):
        s.status = "x"


def test_runtime_report_frozen():
    r = RuntimeReport("r1", "idle")
    with pytest.raises(FrozenInstanceError):
        r.report_id = "x"


def test_rt_status_frozen():
    s = ActivationRuntimeStatus("idle", "idle")
    with pytest.raises(FrozenInstanceError):
        s.overall_status = "x"


def test_runtime_card_frozen():
    c = RuntimeCard("t", "T")
    with pytest.raises(FrozenInstanceError):
        c.card_type = "x"


# --- ActivationRuntimeEngine ---

def test_engine_initial():
    e = ActivationRuntimeEngine()
    s = e.status()
    assert not s.pipeline_running
    assert s.status == "idle"


def test_engine_start():
    e = ActivationRuntimeEngine()
    s = e.start(100.0)
    assert s.pipeline_running
    assert s.current_phase == "building"
    assert s.last_updated == 100.0


def test_engine_register():
    e = ActivationRuntimeEngine()
    e.start()
    from sam.activation.activation_package import ActivationPackage
    pkg = ActivationPackage("pkg_1", "plan", "direct", "seq", ["c1"], 1, 10, 0.9)
    e.register_package(pkg)
    assert e.status().total_packages == 1
    assert len(e.list_packages()) == 1


def test_engine_advance_phase():
    e = ActivationRuntimeEngine()
    e.start()
    e.advance_phase("validated")
    assert e.status().current_phase == "validated"


def test_engine_complete():
    e = ActivationRuntimeEngine()
    e.start()
    e.complete()
    s = e.status()
    assert not s.pipeline_running
    assert s.current_phase == "complete"


# --- ActivationPipeline ---

def test_pipeline_run():
    p = ActivationPipeline()
    ctx = _ctx()
    req = _req()
    pkg = p.run(ctx, req)
    assert pkg.total_candidates >= 1
    assert pkg.strategy_ref != ""
    assert p.engine.status().pipeline_running
    assert p.engine.status().current_phase == "packaged"


def test_pipeline_phases():
    assert len(ActivationPipeline.PIPELINE_PHASES) == 8


# --- ActivationCoordinator ---

def test_coordinator():
    p = ActivationPipeline()
    c = ActivationCoordinator(p)
    assert c.conversation_activation.query_count == 10
    assert c.conversation_validation.query_count == 8
    assert c.conversation_strategy.query_count == 8
    assert c.dashboard_activation.card_count == 6
    assert c.dashboard_monitor.card_count == 5
    assert c.dashboard_runtime.card_count == 5


def test_coordinator_pipeline():
    p = ActivationPipeline()
    c = ActivationCoordinator(p)
    ctx = _ctx()
    req = _req()
    pkg = c.pipeline.run(ctx, req)
    assert pkg.package_id != ""
    s = c.engine.status()
    assert s.total_packages >= 1


# --- RuntimeReport ---

def test_report_builder():
    status = RuntimeStatus(False, "complete", 2, 0, "idle")
    metrics = ActivationMetrics("m", 2, 3, 0.9, 30.0)
    health = ActivationHealthReport(healthy=True, package_count=2, avg_confidence=0.9, event_count=5, issues=[], score=0.9)
    builder = RuntimeReportBuilder()
    report = builder.build("r1", status, metrics, health,
                           ["ctx", "build", "done"])
    assert report.ready_for_execution
    assert report.health_score == 0.9
    assert report.total_packages == 2


def test_report_builder_not_ready():
    status = RuntimeStatus(True, "building", 0, 0, "running")
    metrics = ActivationMetrics("m", 0, 0, 0, 0)
    health = ActivationHealthReport(False, 0, 0, 0, ["No packages"])
    builder = RuntimeReportBuilder()
    report = builder.build("r2", status, metrics, health, ["ctx"])
    assert not report.ready_for_execution
    assert report.total_packages == 0


# --- ActivationRuntimeStatus ---

def test_runtime_status_builder():
    engine_s = RuntimeStatus(False, "complete", 3, 0, "idle")
    health = ActivationHealthReport(True, 3, 0.9, 5, [])
    sb = ActivationRuntimeStatusBuilder()
    s = sb.build(engine_s, health, "complete")
    assert s.overall_status == "ready"
    assert s.ready


def test_runtime_status_builder_not_ready():
    engine_s = RuntimeStatus(True, "building", 0, 0, "running")
    health = ActivationHealthReport(False, 0, 0, 0, ["No packages"])
    sb = ActivationRuntimeStatusBuilder()
    s = sb.build(engine_s, health, "building")
    assert not s.ready


# --- ConversationRuntime ---

def test_conversation_runtime_queries():
    p = ActivationPipeline()
    c = ActivationCoordinator(p)
    conv = ConversationRuntime(c)
    assert conv.query_count == 8


def test_conversation_runtime_status():
    p = ActivationPipeline()
    c = ActivationCoordinator(p)
    conv = ConversationRuntime(c)
    s = conv.query_status()
    assert not s["running"]


def test_conversation_runtime_run():
    p = ActivationPipeline()
    c = ActivationCoordinator(p)
    conv = ConversationRuntime(c)
    ctx = _ctx()
    req = _req()
    result = conv.query_run_pipeline(ctx, req)
    assert result["package_id"] != ""
    assert result["candidates"] >= 1


def test_conversation_runtime_report():
    p = ActivationPipeline()
    c = ActivationCoordinator(p)
    conv = ConversationRuntime(c)
    conv.query_run_pipeline(_ctx(), _req())
    r = conv.query_report()
    assert "report_id" in r
    assert r["packages"] >= 1


def test_conversation_runtime_full_status():
    p = ActivationPipeline()
    c = ActivationCoordinator(p)
    conv = ConversationRuntime(c)
    conv.query_run_pipeline(_ctx(), _req())
    s = conv.query_full_status()
    assert "overall" in s


def test_conversation_packages():
    p = ActivationPipeline()
    c = ActivationCoordinator(p)
    conv = ConversationRuntime(c)
    conv.query_run_pipeline(_ctx(), _req())
    pkgs = conv.query_engine_packages()
    assert len(pkgs) >= 1


def test_conversation_complete():
    p = ActivationPipeline()
    c = ActivationCoordinator(p)
    conv = ConversationRuntime(c)
    conv.query_run_pipeline(_ctx(), _req())
    r = conv.query_complete()
    assert r["status"] == "complete"


# --- DashboardRuntime ---

def test_dashboard_cards():
    p = ActivationPipeline()
    c = ActivationCoordinator(p)
    dash = DashboardRuntime(c)
    assert dash.card_count == 5
    cards = dash.get_cards()
    assert len(cards) == 5
    types = [c.card_type for c in cards]
    assert "status" in types
    assert "pipeline" in types
    assert "report" in types
    assert "packages" in types
    assert "summary" in types


# --- Parametrized ---

# check ActivationContext signature
_actctx_fields = ActivationContext.__dataclass_fields__


@pytest.mark.parametrize("i", list(range(1, 51)))
def test_pipeline_various(i):
    p = ActivationPipeline()
    ctx = ActivationContext(
        context_id=f"ctx_{i}", timestamp=i * 100.0,
        source_plan="plan",
        environment=["normal", "busy", "idle", "emergency"][i % 4],
        total_candidates=i % 6, total_goals=i % 3,
    )
    req = ActivationRequest(f"req_{i}", "plan", i * 100.0, "system",
                            ["low", "normal", "high", "critical"][i % 4])
    pkg = p.run(ctx, req)
    assert pkg.total_candidates >= 1
    assert pkg.strategy_ref in ("direct", "staged", "parallel", "conditional", "fallback")


@pytest.mark.parametrize("i", list(range(1, 41)))
def test_report_various(i):
    pkgs = i % 6
    healthy = i % 3 != 0
    running = i % 4 == 0
    status = RuntimeStatus(running, "phase", pkgs, i * 10.0,
                           "running" if running else "idle")
    metrics = ActivationMetrics("m", pkgs, pkgs, 0.5 + (i % 5) * 0.1, 30.0)
    health = ActivationHealthReport(healthy, pkgs, 0.8, pkgs,
                                    ["test issue"] if not healthy else [])
    builder = RuntimeReportBuilder()
    phases = ["ctx", "build", "validate", "strategy", "package", "monitor", "complete"]
    report = builder.build(f"r{i}", status, metrics, health, phases)
    assert report.report_id == f"r{i}"
    assert report.phases_completed == phases


@pytest.mark.parametrize("i", list(range(1, 31)))
def test_status_builder_various(i):
    pkgs = i % 5
    healthy = i % 2 == 0
    running = i % 3 == 0
    engine_s = RuntimeStatus(running, "phase", pkgs, i * 10.0,
                             "running" if running else "idle")
    health = ActivationHealthReport(healthy, pkgs, 0.8, pkgs, [])
    sb = ActivationRuntimeStatusBuilder()
    s = sb.build(engine_s, health, "phase")
    if not running and healthy and pkgs > 0:
        assert s.overall_status == "ready"
    assert s.phase == "phase"


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
