"""Sprint 89 — Execution Validation Tests."""
import pytest
from dataclasses import FrozenInstanceError
from sam.execution.runtime.execution_context import ExecutionContext
from sam.execution.runtime.execution_request import ExecutionRequest
from sam.execution.runtime.execution_candidate import ExecutionCandidate
from sam.execution.runtime.execution_registry import ExecutionRegistry
from sam.execution.runtime.execution_builder import ExecutionBuilder
from sam.execution.runtime.runtime import ExecutionRuntime, ExecutionDraft
from sam.execution.runtime.execution_validator import (
    ExecutionValidator, ExecutionRules, ExecutionConstraints,
    ExecutionReadiness, ExecutionReportBuilder, ExecutionReport,
    ExecutionValidationError, ExecutionValidationReport,
)
from sam.execution.runtime.conversation_validation import ConversationValidation
from sam.execution.runtime.dashboard_validation import DashboardValidation
from sam.execution.runtime.dashboard_execution import ExecutionCard


# ============================================================
# 1. ExecutionValidator Tests
# ============================================================

class TestExecutionValidator:
    def test_valid_draft(self):
        v = ExecutionValidator()
        draft = ExecutionDraft("d1", "e1", 3, ["immediate"], "test")
        c1 = ExecutionCandidate("c1", "e1", "r1", 1.0, candidate_type="immediate")
        report = v.validate(draft, [c1])
        assert report.valid
        assert report.total_errors == 0

    def test_invalid_empty_draft_id(self):
        v = ExecutionValidator()
        draft = ExecutionDraft("", "e1", 3, ["immediate"], "test")
        c1 = ExecutionCandidate("c1", "e1", "r1", 1.0, candidate_type="immediate")
        report = v.validate(draft, [c1])
        assert not report.valid

    def test_invalid_empty_context_id(self):
        v = ExecutionValidator()
        draft = ExecutionDraft("d1", "", 3, ["immediate"], "test")
        c1 = ExecutionCandidate("c1", "e1", "r1", 1.0, candidate_type="immediate")
        report = v.validate(draft, [c1])
        assert not report.valid

    def test_invalid_no_candidates(self):
        v = ExecutionValidator()
        draft = ExecutionDraft("d1", "e1", 0, [], "empty")
        report = v.validate(draft, [])
        assert not report.valid

    def test_invalid_candidate_type(self):
        v = ExecutionValidator()
        draft = ExecutionDraft("d1", "e1", 2, ["invalid"], "test")
        c1 = ExecutionCandidate("c1", "e1", "r1", 1.0, candidate_type="invalid_type")
        report = v.validate(draft, [c1])
        assert not report.valid
        assert report.total_errors >= 1

    def test_invalid_negative_effort(self):
        v = ExecutionValidator()
        draft = ExecutionDraft("d1", "e1", 2, ["immediate"], "test")
        c1 = ExecutionCandidate("c1", "e1", "r1", 1.0, candidate_type="immediate",
                               estimated_effort=-1.0)
        report = v.validate(draft, [c1])
        assert not report.valid

    def test_validation_error_frozen(self):
        e = ExecutionValidationError("f", "msg", "error")
        with pytest.raises(FrozenInstanceError):
            e.field = "changed"

    def test_validation_report_frozen(self):
        report = ExecutionValidationReport("d1", True, 0, 0, [], "ok")
        with pytest.raises(FrozenInstanceError):
            report.draft_id = "changed"


# ============================================================
# 2. ExecutionRules Tests
# ============================================================

class TestExecutionRules:
    def test_valid_environments(self):
        r = ExecutionRules()
        for env in ["normal", "restricted", "critical"]:
            assert r.validate_environment(env)
        assert not r.validate_environment("invalid")

    def test_valid_task_types(self):
        r = ExecutionRules()
        for t in ["process", "analyze", "generate", "transform"]:
            assert r.validate_task_type(t)
        assert not r.validate_task_type("invalid")

    def test_valid_priorities(self):
        r = ExecutionRules()
        for p in [1, 5, 10]:
            assert r.validate_priority(p)
        assert not r.validate_priority(0)
        assert not r.validate_priority(11)

    def test_valid_effort(self):
        r = ExecutionRules()
        assert r.validate_effort(0.0)
        assert r.validate_effort(100.0)
        assert not r.validate_effort(-1.0)

    def test_valid_candidate_types(self):
        r = ExecutionRules()
        for t in ["immediate", "scheduled", "conditional", "batch", "pipeline"]:
            assert r.validate_candidate_type(t)
        assert not r.validate_candidate_type("invalid")

    def test_count_active_rules(self):
        r = ExecutionRules()
        assert r.count_active_rules() == 6


# ============================================================
# 3. ExecutionConstraints Tests
# ============================================================

class TestExecutionConstraints:
    def test_candidate_count_within(self):
        c = ExecutionConstraints()
        assert c.check_candidate_count(50)
        assert c.check_candidate_count(0)
        assert c.check_candidate_count(100)
        assert not c.check_candidate_count(-1)
        assert not c.check_candidate_count(101)

    def test_dependency_count_within(self):
        c = ExecutionConstraints()
        assert c.check_dependency_count(["a", "b"])
        assert c.check_dependency_count([])
        assert not c.check_dependency_count(["x"] * 21)

    def test_effort_within(self):
        c = ExecutionConstraints()
        assert c.check_effort(0.0)
        assert c.check_effort(500.0)
        assert c.check_effort(1000.0)
        assert not c.check_effort(-0.1)
        assert not c.check_effort(1000.1)

    def test_check_all_no_violations(self):
        c = ExecutionConstraints()
        violations = c.check_all(50, 5, 500.0)
        assert violations == []

    def test_check_all_with_violations(self):
        c = ExecutionConstraints()
        violations = c.check_all(200, 5, 500.0)
        assert len(violations) == 1
        violations = c.check_all(50, 5, 2000.0)
        assert len(violations) == 1

    def test_count_active_constraints(self):
        c = ExecutionConstraints()
        assert c.count_active_constraints() == 4


# ============================================================
# 4. ExecutionReadiness Tests
# ============================================================

class TestExecutionReadiness:
    def test_not_ready_empty(self):
        r = ExecutionReadiness()
        result = r.check()
        assert not result["ready"]
        assert result["score"] == 0.0
        assert result["passed"] == 0

    def test_ready_all_pass(self):
        r = ExecutionReadiness()
        result = r.check(context_exists=True, candidates_ready=True,
                        request_valid=True, validator_passed=True)
        assert result["ready"]
        assert result["score"] == 1.0
        assert result["passed"] == 4

    def test_partial_ready(self):
        r = ExecutionReadiness()
        result = r.check(context_exists=True, candidates_ready=True)
        assert not result["ready"]
        assert result["score"] == 0.5

    def test_check_candidate_ready(self):
        r = ExecutionReadiness()
        c = ExecutionCandidate("c1", "e1", "r1", 1.0)
        assert r.check_candidate(c)
        c2 = ExecutionCandidate("", "e1", "r1", 1.0)
        assert not r.check_candidate(c2)


# ============================================================
# 5. ExecutionReportBuilder Tests
# ============================================================

class TestExecutionReportBuilder:
    def test_build_valid(self):
        v = ExecutionValidator()
        draft = ExecutionDraft("d1", "e1", 2, ["immediate"], "test")
        c1 = ExecutionCandidate("c1", "e1", "r1", 1.0, candidate_type="immediate")
        validation = v.validate(draft, [c1])
        builder = ExecutionReportBuilder()
        report = builder.build("r1", validation, [], {
            "ready": True, "score": 1.0, "checks": {"a": True},
            "passed": 1, "total": 1,
        })
        assert report.overall_valid
        assert "PASS" in report.summary

    def test_build_invalid(self):
        v = ExecutionValidator()
        draft = ExecutionDraft("", "e1", 0, [], "")
        validation = v.validate(draft, [])
        builder = ExecutionReportBuilder()
        report = builder.build("r2", validation, ["no_context"], {
            "ready": False, "score": 0.0, "checks": {},
            "passed": 0, "total": 4,
        })
        assert not report.overall_valid
        assert "FAIL" in report.summary
        assert len(report.constraints) == 1

    def test_report_frozen(self):
        builder = ExecutionReportBuilder()
        report = builder.build("r1", ExecutionValidationReport(), [], {
            "ready": False, "score": 0.0, "checks": {},
            "passed": 0, "total": 4,
        })
        with pytest.raises(FrozenInstanceError):
            report.report_id = "changed"


# ============================================================
# 6. ConversationValidation Tests
# ============================================================

class TestConversationValidation:
    def test_queries(self):
        v = ExecutionValidator()
        rules = ExecutionRules()
        constraints = ExecutionConstraints()
        readiness = ExecutionReadiness()
        conv = ConversationValidation(v, rules, constraints, readiness)
        assert conv.get_validator() is v
        assert conv.get_rules() is rules
        assert conv.get_constraints() is constraints
        assert conv.get_readiness() is readiness
        assert conv.check_environment("normal")
        assert not conv.check_environment("invalid")
        assert conv.check_task_type("process")
        assert not conv.check_task_type("invalid")
        assert conv.check_priority(5)
        assert not conv.check_priority(0)
        assert conv.list_active_rules() == 6


# ============================================================
# 7. DashboardValidation Tests
# ============================================================

class TestDashboardValidation:
    def test_cards_empty(self):
        reg = ExecutionRegistry()
        v = ExecutionValidator()
        rules = ExecutionRules()
        constraints = ExecutionConstraints()
        readiness = ExecutionReadiness()
        dash = DashboardValidation(reg, v, rules, constraints, readiness)
        vc = dash.validator_card()
        assert vc.status == "ready"
        rc = dash.rules_card()
        assert rc.status == "active"
        cc = dash.constraints_card()
        assert cc.metrics["max_candidates"] == 100
        rc2 = dash.readiness_card()
        assert rc2.status == "not_ready"
        vrc = dash.validation_report_card(None)
        assert vrc.status == "empty"

    def test_cards_with_report(self):
        reg = ExecutionRegistry()
        v = ExecutionValidator()
        rules = ExecutionRules()
        constraints = ExecutionConstraints()
        readiness = ExecutionReadiness()
        dash = DashboardValidation(reg, v, rules, constraints, readiness)
        builder = ExecutionReportBuilder()
        report = builder.build("r1", ExecutionValidationReport("d1", True), [], {
            "ready": True, "score": 1.0, "checks": {"a": True},
            "passed": 1, "total": 1,
        })
        vrc = dash.validation_report_card(report)
        assert vrc.status == "passed"
        assert vrc.metrics["valid"]


# ============================================================
# 8. ExecutionRuntime Validation Integration
# ============================================================

class TestRuntimeValidation:
    def test_run_validation_empty(self):
        rt = ExecutionRuntime()
        report = rt.run_validation()
        assert isinstance(report, ExecutionReport)
        assert not report.overall_valid

    def test_run_validation_after_run(self):
        rt = ExecutionRuntime()
        rt.run(ExecutionContext("e1", 1000.0), ExecutionRequest("r1", "e1", 1000.0))
        report = rt.run_validation()
        assert isinstance(report, ExecutionReport)
        assert report.validation is not None

    def test_run_validation_with_props(self):
        rt = ExecutionRuntime()
        ctx = ExecutionContext("e2", 2000.0)
        req = ExecutionRequest("r2", "e2", 2000.0)
        rt.run(ctx, req)
        report = rt.run_validation("normal")
        assert "PASS" in report.summary or "FAIL" in report.summary

    def test_validation_uses_correct_components(self):
        rt = ExecutionRuntime()
        assert rt.validator is not None
        assert rt.rules is not None
        assert rt.constraints is not None
        assert rt.readiness is not None
        assert rt.report_builder is not None


# ============================================================
# 9. Immutability Tests
# ============================================================

def test_all_dtos_frozen():
    """Verifikasi semua DTO immutable."""
    for obj in [
        ExecutionValidationError("f", "m", "error"),
        ExecutionValidationReport("d", True, 0, 0, [], "ok"),
        ExecutionReport("r", "d", None, [], {}, False, "s"),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(obj, list(vars(obj).keys())[0], "x")


# ============================================================
# 10. Forbidden Imports Scan
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
# 11. Parametrized Tests
# ============================================================

@pytest.mark.parametrize("i", list(range(1, 31)))
def test_validator_parametrized(i):
    v = ExecutionValidator()
    envs = ["immediate", "scheduled", "conditional", "batch", "pipeline"]
    t = envs[i % len(envs)]
    draft = ExecutionDraft(f"d{i}", f"e{i}", i, [t], "test")
    c = ExecutionCandidate(f"c{i}", f"e{i}", f"r{i}", float(i), candidate_type=t)
    report = v.validate(draft, [c])
    assert isinstance(report, ExecutionValidationReport)


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_rules_parametrized(i):
    r = ExecutionRules()
    assert r.validate_priority(max(1, min(10, i)))


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_constraints_parametrized(i):
    c = ExecutionConstraints()
    assert c.check_candidate_count(i * 5)
    violations = c.check_all(i * 5, i, float(i * 10))
    assert isinstance(violations, list)


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_readiness_parametrized(i):
    r = ExecutionReadiness()
    result = r.check(
        context_exists=i > 1,
        candidates_ready=i > 3,
        request_valid=i > 5,
        validator_passed=i > 7,
    )
    assert isinstance(result["ready"], bool)
    assert 0.0 <= result["score"] <= 1.0


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_runtime_validation_parametrized(i):
    rt = ExecutionRuntime()
    ctx = ExecutionContext(f"e{i}", float(i * 100))
    req = ExecutionRequest(f"r{i}", f"e{i}", float(i * 100))
    rt.run(ctx, req)
    report = rt.run_validation()
    assert isinstance(report, ExecutionReport)


@pytest.mark.parametrize("i", list(range(1, 11)))
def test_conversation_validation_parametrized(i):
    v = ExecutionValidator()
    rules = ExecutionRules()
    constraints = ExecutionConstraints()
    readiness = ExecutionReadiness()
    conv = ConversationValidation(v, rules, constraints, readiness)
    assert isinstance(conv.list_active_rules(), int)


@pytest.mark.parametrize("i", list(range(1, 16)))
def test_dashboard_validation_parametrized(i):
    reg = ExecutionRegistry()
    for j in range(i):
        reg.register_context(ExecutionContext(f"e{j}", float(j)))
    v = ExecutionValidator()
    dash = DashboardValidation(reg, v, ExecutionRules(),
                               ExecutionConstraints(), ExecutionReadiness())
    rc = dash.readiness_card()
    assert isinstance(rc.metrics["score"], float)
