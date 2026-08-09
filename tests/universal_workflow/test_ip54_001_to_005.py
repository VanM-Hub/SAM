"""Test MISSION-5.4 - Universal Workflow Integration (IP-5.4-001..005).

Coverage: WP-01..WP-50 - foundation, composition, execution, state/recovery,
certification.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.universal_workflow import (
    DependencyResolver,
    ExecutionComplianceChecker,
    FailureRecoveryModel,
    IdempotencyManager,
    LearningEvidenceCollector,
    OutcomeAnalyzer,
    StepDependency,
    StepExecutionResult,
    StepKind,
    WorkflowCertification,
    WorkflowCertStatus,
    WorkflowComplianceChecker,
    WorkflowComposer,
    WorkflowDefinition,
    WorkflowExecutionEngine,
    WorkflowIdentity,
    WorkflowPersistence,
    WorkflowState,
    WorkflowStateMachine,
    WorkflowStep,
    WorkflowValidator,
)

A = WorkflowIdentity(workflow_id="wf-1", name="Sample")


def _definition():
    steps = (WorkflowStep("s1", StepKind.TASK), WorkflowStep("s2", StepKind.TASK), WorkflowStep("s3", StepKind.DECISION))
    deps = (StepDependency("s2", ("s1",)), StepDependency("s3", ("s1", "s2")))
    return WorkflowDefinition(identity=A, steps=steps, inputs=("x",), outputs=("y",), dependencies=deps)


class TestFoundation:
    def test_state_machine(self):
        sm = WorkflowStateMachine("wf-1")
        assert sm.can_transition(WorkflowState.VALIDATED) is True
        sm = sm.transition(WorkflowState.VALIDATED)
        assert sm.state == WorkflowState.VALIDATED

    def test_validation(self):
        assert WorkflowValidator().validate(_definition()).valid is True

    def test_validation_allows_step_output(self):
        # Output bisa dihasilkan oleh step; bukan wajib dari input
        ok = WorkflowDefinition(identity=A, steps=(WorkflowStep("s1"),), inputs=("x",), outputs=("y",), dependencies=())
        assert WorkflowValidator().validate(ok).valid is True

    def test_validation_fails_unknown_dependency(self):
        bad = WorkflowDefinition(identity=A, steps=(WorkflowStep("s1"),), inputs=("x",), outputs=("y",), dependencies=(StepDependency("s1", ("ghost",)),))
        assert WorkflowValidator().validate(bad).valid is False

    def test_persistence(self):
        repo = WorkflowPersistence()
        repo.save_definition(_definition())
        assert repo.load_definition("wf-1") is not None

    def test_compliance(self):
        assert WorkflowComplianceChecker().certify(_definition())["certified"] is True
        assert WorkflowComplianceChecker().certify(_definition(), deterministic=False)["certified"] is False


class TestComposition:
    def test_compose_and_resolve(self):
        composer = WorkflowComposer()
        composer.bind_capability("s1", "read")
        steps = (WorkflowStep("s1"), WorkflowStep("s2"), WorkflowStep("s3"))
        deps = (StepDependency("s2", ("s1",)), StepDependency("s3", ("s1", "s2")))
        definition = composer.compose("wf-c", steps)
        definition = WorkflowDefinition(identity=definition.identity, steps=definition.steps, inputs=definition.inputs, outputs=definition.outputs, dependencies=deps)
        order = DependencyResolver().resolve(steps, deps)
        assert order == ("s1", "s2", "s3")
        assert composer.capability_for("s1") == "read"

    def test_circular_dependency(self):
        steps = (WorkflowStep("a"), WorkflowStep("b"))
        deps = (StepDependency("a", ("b",)), StepDependency("b", ("a",)))
        try:
            DependencyResolver().resolve(steps, deps)
            assert False
        except ValueError:
            pass


class TestExecution:
    def _ctx(self, approved=True):
        return WorkflowExecutionEngine().execute(
            request_id="r1", workflow_id="wf-1", step_ids=("s1", "s2"), require_approval=True, approved=approved
        )

    def test_executes_when_approved(self):
        ctx = self._ctx(approved=True)
        assert ctx.executed is True
        assert ctx.all_passed is True
        assert len(ctx.results) == 2

    def test_blocks_without_approval(self):
        ctx = self._ctx(approved=False)
        assert ctx.executed is False
        assert ctx.all_passed is False

    def test_execution_compliance(self):
        ctx = self._ctx(approved=True)
        assert ExecutionComplianceChecker().certify(ctx)["certified"] is True


class TestStateRecovery:
    def test_checkpoint_resume(self):
        from sam.universal_workflow import RecoveryStateMachine

        sm = RecoveryStateMachine("wf-1")
        sm.checkpoint()
        sm.resume()

    def test_idempotency(self):
        mgr = IdempotencyManager()
        first = mgr.guard_for("r1")
        second = mgr.guard_for("r1")
        assert first.already_executed is False
        assert second.already_executed is True

    def test_outcome_and_evidence(self):
        engine = WorkflowExecutionEngine()
        ok = engine.execute(request_id="a", workflow_id="wf-1", step_ids=("s1",), require_approval=True, approved=True)
        contexts = (ok,)
        outcome = OutcomeAnalyzer().analyze("wf-1", contexts)
        assert outcome.completed == 1
        evidence = LearningEvidenceCollector().collect(outcome)
        assert evidence.outcome == "healthy"

    def test_failure_classify(self):
        model = FailureRecoveryModel()
        assert model.classify(StepExecutionResult("s1", False, error="retryable")) == "retryable"
        assert model.classify(StepExecutionResult("s1", False, error="fatal")) == "fatal"


class TestCertification:
    def test_full_certified(self):
        cert = WorkflowCertification()
        cert.foundation_certification()
        cert.composition_certification()
        cert.execution_certification()
        cert.state_recovery_certification()
        cert.governance_certification()
        cert.determinism_certification()
        cert.failure_certification()
        cert.audit_certification()
        cert.regression_compliance()
        cert.mission_certification()
        result = cert.certify()
        assert result["certified"] is True
        assert result["status"] == WorkflowCertStatus.CERTIFIED.value

    def test_not_certified(self):
        cert = WorkflowCertification()
        cert.determinism_certification(deterministic=False, idempotent=False)
        cert.governance_certification(no_authority=False, governed=False)
        assert cert.certify()["status"] == WorkflowCertStatus.NOT_CERTIFIED.value
