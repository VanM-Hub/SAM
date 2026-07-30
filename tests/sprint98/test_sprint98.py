"""Sprint 98 — Execution Quality & Validation Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.quality import QualityMetric, QualityAssessment, QualityGate, QualitySummary
from sam.execution.runtime.quality_engine import QualityEngine
from sam.execution.runtime.conversation_quality import ConversationQuality, DashboardQuality
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. Quality DTO Tests
# ============================================================

class TestQualityMetric:
    def test_create(self):
        m = QualityMetric("effort_variance", 0.85, weight=1.0, description="Good")
        assert m.name == "effort_variance"
        assert m.score == 0.85
        assert m.weight == 1.0

    def test_immutable(self):
        m = QualityMetric("n", 0.0)
        with pytest.raises(FrozenInstanceError):
            m.score = 0.9


class TestQualityAssessment:
    def test_create(self):
        a = QualityAssessment("qa1", "ep1", overall_score=0.85)
        assert a.assessment_id == "qa1"
        assert a.overall_score == 0.85

    def test_with_metrics(self):
        m = (QualityMetric("m1", 0.9, 1.0),)
        a = QualityAssessment("qa1", "ep1", metrics=m, overall_score=0.9, total_weight=1.0)
        assert len(a.metrics) == 1

    def test_immutable(self):
        a = QualityAssessment("qa", "ep")
        with pytest.raises(FrozenInstanceError):
            a.overall_score = 1.0


class TestQualityGate:
    def test_defaults(self):
        g = QualityGate("g1", "gate")
        assert g.threshold == 0.8
        assert not g.passed

    def test_passed(self):
        g = QualityGate("g1", "gate", threshold=0.8, passed=True, score=0.9)
        assert g.passed
        assert g.score == 0.9

    def test_immutable(self):
        g = QualityGate("g1", "gate")
        with pytest.raises(FrozenInstanceError):
            g.passed = True


class TestQualitySummary:
    def test_defaults(self):
        s = QualitySummary()
        assert s.status == "unknown"

    def test_failed(self):
        s = QualitySummary(gates_failed=1, status="gates_failed")
        assert s.gates_failed == 1

    def test_immutable(self):
        s = QualitySummary()
        with pytest.raises(FrozenInstanceError):
            s.status = "gates_passed"


# ============================================================
# 2. QualityEngine Tests
# ============================================================

class TestQualityEngine:
    def test_assess_empty(self):
        e = QualityEngine()
        a = e.assess("qa1", "ep1", [])
        assert a.overall_score == 0.0

    def test_assess_with_candidates(self):
        e = QualityEngine()
        c = [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=10.0,
                               candidate_type="task")]
        a = e.assess("qa1", "ep1", c)
        assert a.overall_score > 0
        assert a.total_weight > 0
        assert len(a.metrics) == 3

    def test_assess_diversity(self):
        e = QualityEngine()
        c = [
            ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=5.0,
                              candidate_type="task"),
            ExecutionCandidate("c2", "e1", "r1", 1.0, estimated_effort=10.0,
                              candidate_type="batch"),
            ExecutionCandidate("c3", "e1", "r1", 1.0, estimated_effort=15.0,
                              candidate_type="pipeline"),
        ]
        a = e.assess("qa1", "ep1", c)
        assert a.overall_score > 0

    def test_create_gate(self):
        e = QualityEngine()
        g = e.create_gate("g1", "Execution Gate", threshold=0.75)
        assert g.gate_id == "g1"
        assert g.threshold == 0.75

    def test_evaluate_gate_pass(self):
        e = QualityEngine()
        e.create_gate("g1", "Execution Gate")
        g = e.evaluate_gate("g1", 0.9)
        assert g.passed
        assert g.score == 0.9

    def test_evaluate_gate_fail(self):
        e = QualityEngine()
        e.create_gate("g1", "Execution Gate")
        g = e.evaluate_gate("g1", 0.5)
        assert not g.passed
        assert len(g.failures) == 1

    def test_evaluate_gate_missing(self):
        e = QualityEngine()
        g = e.evaluate_gate("bogus", 0.9)
        assert g.name == "unknown"

    def test_summary_empty(self):
        e = QualityEngine()
        s = e.get_summary()
        assert s.total_assessments == 0
        assert s.status == "unknown"

    def test_summary_with_data(self):
        e = QualityEngine()
        c = [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=10.0)]
        e.assess("qa1", "ep1", c)
        s = e.get_summary()
        assert s.total_assessments == 1

    def test_summary_gates_failed(self):
        e = QualityEngine()
        e.create_gate("g1", "Gate")
        e.evaluate_gate("g1", 0.3)
        s = e.get_summary()
        assert s.gates_failed == 1
        assert s.status == "gates_failed"

    def test_summary_gates_passed(self):
        e = QualityEngine()
        e.create_gate("g1", "Gate")
        e.evaluate_gate("g1", 0.95)
        s = e.get_summary()
        assert s.gates_passed == 1
        assert s.status == "gates_passed"


# ============================================================
# 3. ConversationQuality Tests
# ============================================================

class TestConversationQuality:
    def test_queries(self):
        cq = ConversationQuality(QualityEngine())
        assert cq.get_engine() is not None
        caps = cq.describe_capabilities()
        assert len(caps) >= 5
        assert cq.count_capabilities() >= 5
        names = cq.get_metric_names()
        assert len(names) == 3
        assert cq.count_metrics() == 3


# ============================================================
# 4. DashboardQuality Tests
# ============================================================

class TestDashboardQuality:
    def test_cards(self):
        dq = DashboardQuality(QualityEngine())
        ec = dq.engine_card()
        assert ec.status == "ready"
        ac = dq.assessment_card()
        assert ac.status == "unknown"
        gc = dq.gate_card()
        assert gc.status == "unknown"
        mc = dq.metrics_card()
        assert mc.status == "ready"
        sc = dq.summary_card()
        assert sc.status == "unknown"

    def test_cards_with_data(self):
        e = QualityEngine()
        c = [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=10.0)]
        e.assess("qa1", "ep1", c)
        dq = DashboardQuality(e)
        ac = dq.assessment_card()
        assert ac.metrics["total"] >= 1

    def test_all_frozen(self):
        dq = DashboardQuality(QualityEngine())
        for card in [dq.engine_card(), dq.assessment_card(), dq.gate_card(),
                     dq.metrics_card(), dq.summary_card()]:
            with pytest.raises(FrozenInstanceError):
                card.title = "changed"


# ============================================================
# 5. Immutability
# ============================================================

def test_all_dtos_frozen():
    for obj in [QualityMetric("n", 0.0), QualityAssessment("qa", "ep"),
                QualityGate("g", "n"), QualitySummary()]:
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

@pytest.mark.parametrize("i", list(range(1, 36)))
def test_assess_parametrized(i):
    e = QualityEngine()
    c = [ExecutionCandidate(f"c{j}", "e1", "r1", float(j), estimated_effort=float(j * 3))
         for j in range(i % 5 + 1)]
    a = e.assess(f"qa{i}", "ep1", c)
    assert a.overall_score >= 0


@pytest.mark.parametrize("i", list(range(1, 21)))
def test_gate_parametrized(i):
    e = QualityEngine()
    e.create_gate(f"g{i}", f"Gate {i}", threshold=float(i % 10) / 10.0 + 0.1)
    g = e.evaluate_gate(f"g{i}", float(i) / 10.0)
    assert isinstance(g.passed, bool)


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_summary_parametrized(i):
    e = QualityEngine()
    for j in range(i % 5 + 1):
        e.assess(f"qa{j}", "ep1",
                [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=float(j * 3))])
    s = e.get_summary()
    assert s.total_assessments == i % 5 + 1


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_quality_parametrized(i):
    e = QualityEngine()
    for j in range(i):
        e.assess(f"qa{j}", "ep1",
                [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=float(j))])
    cq = ConversationQuality(e)
    assert cq.count_assessments() == i


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_quality_parametrized(i):
    e = QualityEngine()
    for j in range(i % 4):
        e.assess(f"qa{j}", "ep1",
                [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=float(j * 2))])
    dq = DashboardQuality(e)
    c = dq.assessment_card()
    assert c.metrics["total"] == i % 4


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_metric_fields_parametrized(i):
    e = QualityEngine()
    c = [ExecutionCandidate("c1", "e1", "r1", 1.0, estimated_effort=float(i * 5))]
    a = e.assess("qa1", "ep1", c)
    assert len(a.metrics) == 3
