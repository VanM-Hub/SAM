"""Sprint 97 — Execution Risk Engine Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.risk import RiskFactor, RiskAssessment, RiskReport, RiskSummary
from sam.execution.runtime.risk_engine import RiskEngine
from sam.execution.runtime.conversation_risk import ConversationRisk, DashboardRisk
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. Risk DTO Tests
# ============================================================

class TestRiskFactor:
    def test_create(self):
        f = RiskFactor("high_effort", 0.8, "Effort > 100")
        assert f.name == "high_effort"
        assert f.score == 0.8
        assert f.description == "Effort > 100"

    def test_immutable(self):
        f = RiskFactor("n", 0.0)
        with pytest.raises(FrozenInstanceError):
            f.score = 0.9


class TestRiskAssessment:
    def test_create(self):
        a = RiskAssessment("ra1", candidate_id="c1", overall_score=0.6, level="medium")
        assert a.assessment_id == "ra1"
        assert a.overall_score == 0.6
        assert a.level == "medium"

    def test_with_factors(self):
        f = (RiskFactor("f1", 0.5),)
        a = RiskAssessment("ra1", candidate_id="c1", factors=f, overall_score=0.5)
        assert len(a.factors) == 1

    def test_immutable(self):
        a = RiskAssessment("ra", "c")
        with pytest.raises(FrozenInstanceError):
            a.level = "critical"


class TestRiskReport:
    def test_create(self):
        r = RiskReport("rr1", "ep1", total_assessments=3, highest_risk=0.9)
        assert r.report_id == "rr1"
        assert r.highest_risk == 0.9

    def test_immutable(self):
        r = RiskReport("rr", "ep")
        with pytest.raises(FrozenInstanceError):
            r.highest_risk = 1.0


class TestRiskSummary:
    def test_defaults(self):
        s = RiskSummary()
        assert s.status == "low_risk"
        assert s.total_assessments == 0

    def test_critical(self):
        s = RiskSummary(critical_count=1, status="critical_risk")
        assert s.critical_count == 1
        assert s.status == "critical_risk"

    def test_immutable(self):
        s = RiskSummary()
        with pytest.raises(FrozenInstanceError):
            s.status = "critical_risk"


# ============================================================
# 2. RiskEngine Tests
# ============================================================

class TestRiskEngine:
    def test_assess_low(self):
        r = RiskEngine()
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=10.0)
        a = r.assess(c)
        assert a.level in ("low", "medium")

    def test_assess_high_effort(self):
        r = RiskEngine()
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=200.0)
        a = r.assess(c)
        assert any(f.name == "high_effort" for f in a.factors)

    def test_assess_many_deps(self):
        r = RiskEngine()
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=10.0,
                              dependencies=[f"d{i}" for i in range(10)])
        a = r.assess(c)
        assert any("many" in f.name for f in a.factors)

    def test_assess_high_priority(self):
        r = RiskEngine()
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=10.0,
                              metadata={"priority": 9.0})
        a = r.assess(c)
        assert any("high_priority" in f.name for f in a.factors)

    def test_assess_batch(self):
        r = RiskEngine()
        c = [ExecutionCandidate(f"c{i}", "e1", "r1", float(i), estimated_effort=float(i * 10))
             for i in range(5)]
        assessments = r.assess_batch(c)
        assert len(assessments) == 5

    def test_level_low(self):
        r = RiskEngine()
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=1.0)
        a = r.assess(c)
        assert a.level == "low"

    def test_level_high(self):
        r = RiskEngine()
        c = ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=60.0,
                              dependencies=[f"d{i}" for i in range(10)],
                              metadata={"priority": 9.0})
        a = r.assess(c)
        assert a.level in ("high", "critical")

    def test_generate_report(self):
        r = RiskEngine()
        c = [ExecutionCandidate(f"c{i}", "e1", "r1", float(i), estimated_effort=float(i * 10))
             for i in range(3)]
        report = r.generate_report("rr1", "ep1", c)
        assert report.total_assessments == 3
        assert report.highest_risk > 0
        assert report.avg_risk > 0

    def test_summary_empty(self):
        r = RiskEngine()
        s = r.get_summary()
        assert s.total_assessments == 0

    def test_summary_with_data(self):
        r = RiskEngine()
        r.assess(ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=10.0))
        s = r.get_summary()
        assert s.total_assessments == 1

    def test_summary_critical(self):
        r = RiskEngine()
        r.assess(ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=200.0,
                                   dependencies=[f"d{i}" for i in range(10)],
                                   metadata={"priority": 9.0}))
        s = r.get_summary()
        assert s.critical_count > 0 or s.high_count > 0


# ============================================================
# 3. ConversationRisk Tests
# ============================================================

class TestConversationRisk:
    def test_queries(self):
        cr = ConversationRisk(RiskEngine())
        assert cr.get_engine() is not None
        caps = cr.describe_capabilities()
        assert len(caps) >= 5
        assert cr.count_capabilities() >= 5
        levels = cr.get_supported_levels()
        assert len(levels) == 4
        assert cr.count_levels() == 4


# ============================================================
# 4. DashboardRisk Tests
# ============================================================

class TestDashboardRisk:
    def test_cards(self):
        dr = DashboardRisk(RiskEngine())
        ec = dr.engine_card()
        assert ec.status == "ready"
        ac = dr.assessment_card()
        assert ac.status == "low_risk"
        rc = dr.report_card()
        assert rc.status == "low_risk"
        lc = dr.levels_card()
        assert lc.status == "ready"
        sc = dr.summary_card()
        assert sc.status == "low_risk"

    def test_all_frozen(self):
        dr = DashboardRisk(RiskEngine())
        for card in [dr.engine_card(), dr.assessment_card(), dr.report_card(),
                     dr.levels_card(), dr.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [RiskFactor("n", 0.0), RiskAssessment("r", "c"),
                RiskReport("r", "ep"), RiskSummary()]:
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
        src_dir = pathlib.Path("src/sam/execution/runtime")
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

@pytest.mark.parametrize("i", list(range(1, 26)))
def test_assess_parametrized(i):
    r = RiskEngine()
    c = ExecutionCandidate(f"c{i}", "e1", "r1", float(i), estimated_effort=float(i * 3))
    a = r.assess(c)
    assert a.overall_score > 0


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_levels_parametrized(i):
    r = RiskEngine()
    c = ExecutionCandidate(f"c{i}", "e1", "r1", float(i),
                          estimated_effort=float(i * 10),
                          metadata={"priority": float(i % 10)})
    a = r.assess(c)
    assert a.level in ("low", "medium", "high", "critical")


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_report_parametrized(i):
    r = RiskEngine()
    c = [ExecutionCandidate(f"c{j}", "e1", "r1", float(j), estimated_effort=float(j * 5))
         for j in range(i % 5 + 1)]
    report = r.generate_report(f"rr{i}", "ep1", c)
    assert report.total_assessments == len(c)


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_summary_parametrized(i):
    r = RiskEngine()
    for j in range(i % 5 + 1):
        r.assess(ExecutionCandidate(f"c{j}", "e1", "r1", float(j),
                                    estimated_effort=float((j + 1) * 3)))
    s = r.get_summary()
    assert s.total_assessments == i % 5 + 1


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_risk_parametrized(i):
    r = RiskEngine()
    for j in range(i):
        r.assess(ExecutionCandidate(f"c{j}", "e1", "r1", float(j),
                                    estimated_effort=float((j + 1) * 5)))
    cr = ConversationRisk(r)
    assert cr.count_assessments() == i


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_risk_parametrized(i):
    r = RiskEngine()
    for j in range(i % 4):
        r.assess(ExecutionCandidate(f"c{j}", "e1", "r1", float(j),
                                    estimated_effort=float((j + 1) * 3)))
    dr = DashboardRisk(r)
    c = dr.assessment_card()
    assert c.metrics["total"] == i % 4


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_effort_risk_parametrized(i):
    r = RiskEngine()
    c = ExecutionCandidate("c1", "e1", "r1", float(i), estimated_effort=float(i * 10))
    a = r.assess(c)
    assert any("effort" in f.name for f in a.factors)
