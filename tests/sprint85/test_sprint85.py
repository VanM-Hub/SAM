import os, sys, pytest
from dataclasses import FrozenInstanceError
import ast

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sam.activation.activation_package import ActivationPackage
from sam.activation.package_builder import PackageBuilder
from sam.activation.package_validator import PackageValidator, PackageValidation
from sam.activation.package_registry import PackageRegistry
from sam.activation.package_export import PackageExporter, PackageExport
from sam.activation.conversation_package import ConversationPackage
from sam.activation.dashboard_package import DashboardPackage, PackageCard
from sam.activation.activation_sequence import ActivationSequence, ActivationStep
from sam.activation.activation_strategy import ActivationStrategy
from sam.activation.activation_candidate import ActivationCandidate


# Helpers
def _seq(steps=3):
    return ActivationSequence(
        sequence_id="seq_test", total_steps=steps,
        steps=[ActivationStep(f"s{i}", i, f"c{i}") for i in range(steps)],
        strategy_ref="direct", duration_estimate=30.0,
    )


def _strat():
    return ActivationStrategy("direct", "Direct", "sequential", 0.95)


def _pkg(status="built"):
    return ActivationPackage("pkg_01", "plan_01", "direct", "seq_test",
                             ["c1", "c2"], 2, 30.0, 0.95, status)


# --- Frozen DTOs ---

def test_package_frozen():
    p = _pkg()
    with pytest.raises(FrozenInstanceError):
        p.package_id = "x"


def test_validation_frozen():
    v = PackageValidation("pkg_01", True)
    with pytest.raises(FrozenInstanceError):
        v.package_id = "x"


def test_export_frozen():
    e = PackageExport("pkg_01")
    with pytest.raises(FrozenInstanceError):
        e.package_id = "x"


def test_package_card_frozen():
    c = PackageCard("t", "T")
    with pytest.raises(FrozenInstanceError):
        c.card_type = "x"


# --- PackageBuilder ---

def test_package_builder():
    b = PackageBuilder()
    pkg = b.build(_seq(), _strat(), "plan_ref")
    assert pkg.total_candidates == 3
    assert pkg.confidence == 0.95
    assert pkg.strategy_ref == "direct"
    assert pkg.status == "built"
    assert "pkg_" in pkg.package_id


# --- PackageValidator ---

def test_package_validator_valid():
    v = PackageValidator()
    val = v.validate(_pkg())
    assert val.valid


def test_package_validator_invalid():
    v = PackageValidator()
    bad = ActivationPackage(package_id="", total_candidates=0, confidence=0)
    val = v.validate(bad)
    assert not val.valid
    assert len(val.errors) > 0


def test_package_validator_candidates():
    v = PackageValidator()
    pkg = ActivationPackage("p1", "plan", "strat", "seq")
    val = v.validate(pkg)
    assert not val.has_candidates


def test_package_validator_no_id():
    v = PackageValidator()
    pkg = ActivationPackage("", "plan", "strat", "seq", ["c1"], 1, 10, 0.8)
    val = v.validate(pkg)
    assert not val.valid


# --- PackageRegistry ---

def test_package_registry():
    reg = PackageRegistry()
    assert reg.count == 0
    reg.register(_pkg())
    assert reg.count == 1
    assert reg.get("pkg_01") is not None


def test_package_registry_list():
    reg = PackageRegistry()
    reg.register(_pkg("built"))
    reg.register(ActivationPackage("pkg_02", "plan_02"))
    assert len(reg.list()) == 2


def test_package_registry_validation():
    reg = PackageRegistry()
    val = PackageValidation("pkg_01", True)
    reg.register_validation("pkg_01", val)
    assert reg.get_validation("pkg_01") is not None
    assert reg.get_validation("x") is None


def test_package_registry_clear():
    reg = PackageRegistry()
    reg.register(_pkg())
    reg.clear()
    assert reg.count == 0


# --- PackageExporter ---

def test_package_exporter():
    ex = PackageExporter()
    exp = ex.export(_pkg())
    assert exp.format == "json"
    assert exp.content["package_id"] == "pkg_01"
    assert exp.content["total_candidates"] == 2


def test_package_exporter_summary():
    ex = PackageExporter()
    pkgs = [_pkg("built"), _pkg("ready")]
    s = ex.export_summary(pkgs)
    assert s["total_packages"] == 2
    assert s["total_candidates"] == 4
    assert s["avg_confidence"] == 0.95


# --- ConversationPackage ---

def test_conversation_package_queries():
    reg = PackageRegistry()
    conv = ConversationPackage(reg)
    assert conv.query_count == 8


def test_conversation_package_build():
    reg = PackageRegistry()
    conv = ConversationPackage(reg)
    b = PackageBuilder()
    result = conv.query_build(b, _seq(), _strat())
    assert result["status"] == "built"
    assert result["total_candidates"] == 3
    assert reg.count == 1


def test_conversation_package_get():
    reg = PackageRegistry()
    reg.register(_pkg())
    conv = ConversationPackage(reg)
    p = conv.query_package("pkg_01")
    assert p is not None
    assert p["package_id"] == "pkg_01"
    assert conv.query_package("x") is None


def test_conversation_package_list():
    reg = PackageRegistry()
    reg.register(_pkg())
    conv = ConversationPackage(reg)
    lst = conv.query_list()
    assert len(lst) == 1


def test_conversation_package_validate():
    reg = PackageRegistry()
    conv = ConversationPackage(reg)
    v = PackageValidator()
    result = conv.query_validate(v, _pkg())
    assert result["valid"]
    assert result["has_candidates"]


def test_conversation_package_validation_status():
    reg = PackageRegistry()
    conv = ConversationPackage(reg)
    assert conv.query_validation_status("pkg_01") is None
    v = PackageValidator()
    conv.query_validate(v, _pkg())
    status = conv.query_validation_status("pkg_01")
    assert status is not None
    assert status["valid"]


def test_conversation_package_export():
    reg = PackageRegistry()
    conv = ConversationPackage(reg)
    ex = PackageExporter()
    result = conv.query_export(ex, _pkg())
    assert result["package_id"] == "pkg_01"
    assert "content" in result


def test_conversation_package_count():
    reg = PackageRegistry()
    reg.register(_pkg())
    conv = ConversationPackage(reg)
    cnt = conv.query_package_count()
    assert cnt["total"] == 1


# --- DashboardPackage ---

def test_dashboard_cards():
    reg = PackageRegistry()
    dash = DashboardPackage(reg)
    assert dash.card_count == 5
    b = PackageBuilder()
    cards = dash.get_cards(b, _seq(), _strat())
    assert len(cards) == 5
    types = [c.card_type for c in cards]
    assert "package" in types
    assert "validation" in types
    assert "registry" in types
    assert "export" in types
    assert "summary" in types


# --- Parametrized ---

@pytest.mark.parametrize("i", list(range(1, 56)))
def test_package_builder_various(i):
    b = PackageBuilder()
    steps = (i % 10) + 1
    seq = ActivationSequence(
        sequence_id=f"seq_{i}", total_steps=steps,
        steps=[ActivationStep(f"s{j}", j, f"c{j}") for j in range(steps)],
        strategy_ref="direct", duration_estimate=i * 10.0,
    )
    conf = min(0.99, max(0.1, i / 10))
    strat = ActivationStrategy(f"str_{i % 5}", f"Strat{i}", "sequential", conf)
    pkg = b.build(seq, strat, f"plan_{i}")
    assert pkg.total_candidates == steps
    assert pkg.confidence == conf
    assert pkg.strategy_ref in ("str_0", "str_1", "str_2", "str_3", "str_4")


@pytest.mark.parametrize("i", list(range(1, 45)))
def test_package_validator_various(i):
    v = PackageValidator()
    has_c = i % 2 == 0
    has_s = i % 3 != 0
    has_strat = i % 4 != 0
    conf = max(0.05, i / 10) if i % 5 != 0 else 0.0

    pkg = ActivationPackage(
        package_id=f"pkg_{i}" if i % 6 != 0 else "",
        plan_ref="plan",
        strategy_ref="strat" if has_strat else "",
        sequence_ref="seq" if has_s else "",
        candidate_refs=["c1"] if has_c else [],
        total_candidates=1 if has_c else 0,
        confidence=conf,
    )
    val = v.validate(pkg)
    assert val.package_id == pkg.package_id


# --- Forbidden imports & AST ---

FORBIDDEN = [
    'sam.guardian', 'sam.approval', 'sam.execution', 'sam.conversation',
    'sam.storage', 'sam.domain', 'sam.repository',
    'sam.operational_brain',
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
    assert not bad, f"Forbidden imports: {bad}"


def test_ast_parse():
    for path in _all_files():
        with open(path, 'r', encoding='utf-8') as fh:
            ast.parse(fh.read(), filename=path)
