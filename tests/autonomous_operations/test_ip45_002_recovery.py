"""Test IP-4.5-002 - Autonomous Recovery (MISSION-4.5).

Coverage: WP-11..WP-20 - recovery planning, validation, execution
(approval-gated), verification, self-debugging, optimization, API,
explainability, compliance, e2e.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.autonomous_operations.recovery_planning import (
    RecoveryPlan,
    RecoveryPlanner,
    RecoveryValidator,
)
from sam.autonomous_operations.recovery_execution import (
    RecoveryExecutor,
)
from sam.autonomous_operations.recovery_verification import (
    RecoveryVerifier,
    SelfDebugging,
)
from sam.autonomous_operations.operational_optimization import OperationalOptimizer
from sam.autonomous_operations.recovery_api import RecoveryAPI
from sam.autonomous_operations.recovery_compliance import (
    RecoveryComplianceChecker,
)


# ---------------------------------------------------------------------------
# WP-11 Recovery Planning
# ---------------------------------------------------------------------------

class TestRecoveryPlanning:
    def test_plan_generated(self):
        planner = RecoveryPlanner()
        plan = planner.plan("inv-1", detected_issues=("provider degraded",))
        assert plan.plan_id
        assert plan.requires_approval is True
        assert len(plan.steps) == 1

    def test_plan_risk_level(self):
        planner = RecoveryPlanner()
        high = planner.plan("inv-1", detected_issues=("x",), severity="critical")
        assert high.risk_level == "high"
        low = planner.plan("inv-1", detected_issues=("x",), severity="info")
        assert low.risk_level == "low"


# ---------------------------------------------------------------------------
# WP-12 Recovery Validation
# ---------------------------------------------------------------------------

class TestRecoveryValidation:
    def test_valid_plan(self):
        plan = RecoveryPlanner().plan("inv-1", detected_issues=("cpu high",))
        result = RecoveryValidator.validate(plan)
        assert result.valid is True

    def test_requires_approval(self):
        plan = RecoveryPlan(
            plan_id="p1", investigation_id="inv-1", requires_approval=False
        )
        result = RecoveryValidator.validate(plan)
        assert not result.valid


# ---------------------------------------------------------------------------
# WP-13 Recovery Execution (approval-gated)
# ---------------------------------------------------------------------------

class TestRecoveryExecution:
    def test_execution_requires_approval(self):
        executor = RecoveryExecutor()
        plan = RecoveryPlanner().plan("inv-1", detected_issues=("cpu",))
        session = executor.create_session(plan)
        with pytest.raises(PermissionError):
            executor.execute(session, plan, approved=False)

    def test_execution_with_approval(self):
        executor = RecoveryExecutor()
        plan = RecoveryPlanner().plan("inv-1", detected_issues=("cpu high",))
        session = executor.create_session(plan)
        done = executor.execute(session, plan, approved=True)
        assert done.status == "completed"
        assert len(done.executed) == 1
        assert done.executed[0].status == "executed"

    def test_execution_audited(self):
        executor = RecoveryExecutor()
        plan = RecoveryPlanner().plan("inv-1", detected_issues=("x",))
        session = executor.create_session(plan)
        executor.execute(session, plan, approved=True)
        assert executor.audit()["session_count"] >= 1


# ---------------------------------------------------------------------------
# WP-14 Recovery Verification
# ---------------------------------------------------------------------------

class TestRecoveryVerification:
    def test_verify_completed(self):
        executor = RecoveryExecutor()
        plan = RecoveryPlanner().plan("inv-1", detected_issues=("cpu",))
        session = executor.create_session(plan)
        done = executor.execute(session, plan, approved=True)
        result = RecoveryVerifier.verify(done)
        assert result.verified is True


class TestSelfDebugging:
    def test_inspect_finds_issues(self):
        state = {"runtime": "critical", "provider": "ok"}
        result = SelfDebugging.inspect(state)
        assert result["clean"] is False
        assert len(result["findings"]) == 1

    def test_inspect_clean(self):
        result = SelfDebugging.inspect({"a": "ok", "b": "healthy"})
        assert result["clean"] is True


# ---------------------------------------------------------------------------
# WP-16 Operational Optimization
# ---------------------------------------------------------------------------

class TestOperationalOptimization:
    def test_suggest_for_high_cpu(self):
        suggestions = OperationalOptimizer.suggest(
            high_cpu_targets=("runtime-a",),
            evidence_ids=(("runtime-a", "e1"),),
        )
        assert len(suggestions) == 1
        assert suggestions[0].evidence_ids == ("e1",)

    def test_suggest_for_provider(self):
        suggestions = OperationalOptimizer.suggest(
            low_availability_providers=("provider-b",)
        )
        assert len(suggestions) == 1
        assert "provider" in suggestions[0].suggestion.lower()


# ---------------------------------------------------------------------------
# WP-17 Recovery API
# ---------------------------------------------------------------------------

class TestRecoveryAPI:
    def test_full_recovery_flow(self):
        api = RecoveryAPI(
            planner=RecoveryPlanner(), executor=RecoveryExecutor()
        )
        plan = api.plan("inv-1", ("cpu high",), severity="warning")
        assert plan.requires_approval
        with pytest.raises(PermissionError):
            api.execute(plan, approved=False)
        session = api.execute(plan, approved=True)
        assert session.status == "completed"
        assert api.verify(session)["verified"] is True


# ---------------------------------------------------------------------------
# WP-18/19 Explainability & Compliance
# ---------------------------------------------------------------------------

class TestRecoveryCompliance:
    def test_explain_has_rationale(self):
        api = RecoveryAPI(planner=RecoveryPlanner(), executor=RecoveryExecutor())
        plan = api.plan("inv-1", ("cpu",))
        expl = api.explain(plan)
        assert expl["approval_required"] is True
        assert len(expl["step_rationale"]) == 1

    def test_certify_clean(self):
        checker = RecoveryComplianceChecker()
        assert checker.certify()["certified"] is True

    def test_detects_no_approval(self):
        checker = RecoveryComplianceChecker()
        assert not checker.certify(approval_before_execution=False)["certified"]

    def test_detects_forbidden(self):
        checker = RecoveryComplianceChecker()
        assert not checker.certify(source="gate.execute(")["certified"]


# ---------------------------------------------------------------------------
# WP-20 Integration & Certification (end-to-end)
# ---------------------------------------------------------------------------

class TestAutonomousRecoveryEndToEnd:
    def test_end_to_end_recovery(self):
        api = RecoveryAPI(planner=RecoveryPlanner(), executor=RecoveryExecutor())

        # Plan dari investigasi (detected issues)
        plan = api.plan("inv-1", ("provider degraded", "cpu high"), severity="critical")
        assert plan.risk_level == "high"
        assert len(plan.steps) == 2

        # Eksekusi butuh approval
        with pytest.raises(PermissionError):
            api.execute(plan, approved=False)

        # Eksekusi dengan approval
        session = api.execute(plan, approved=True)
        assert session.status == "completed"
        assert len(session.executed) == 2

        # Verification
        ver = api.verify(session)
        assert ver["verified"] is True

        # Self-diagnostic
        diag = SelfDebugging.inspect({"provider": "restored", "runtime": "critical"})
        assert diag["clean"] is False

        # Optimisasi berbasis evidence
        opts = OperationalOptimizer.suggest(
            high_cpu_targets=("runtime-a",),
            evidence_ids=(("runtime-a", "e9"),),
        )
        assert opts

        # Compliance penuh
        checker = RecoveryComplianceChecker()
        assert checker.certify()["certified"] is True
        assert not checker.certify(approval_before_execution=False)["certified"]
