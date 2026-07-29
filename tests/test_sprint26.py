import types
from sam.operations.brain.guardian import (
    OperationalPolicyEngine,
    DecisionGate,
    GuardianAudit,
    GuardianStateHolder,
    GuardianDashboardService,
    GuardianRuntimeIntegration,
    GuardianCoordinator,
)


def test_policy_defaults():
    pe = OperationalPolicyEngine()
    policies = pe.policies
    assert len(policies) >= 5


def test_audit_append_and_query():
    a = GuardianAudit()
    a.clear()
    e1 = a.log_gate_passed("p1")
    e2 = a.log_gate_rejected("p2")
    assert a.total_entries == 2
    by_type = a.get_entries_by_type("gate_rejected")
    assert len(by_type) == 1


def test_dashboard_service_returns_dashboard():
    state_holder = GuardianStateHolder()
    audit = GuardianAudit()
    policy_engine = OperationalPolicyEngine()
    svc = GuardianDashboardService(None, None, policy_engine, state_holder, audit)
    db = svc.get_dashboard()
    assert db.summary.total_decisions == 0
    assert hasattr(db, "timestamp")


def test_gate_rejects_on_low_confidence():
    pe = OperationalPolicyEngine()
    gate = DecisionGate(pe)

    class Eval:
        confidence = 0.1
        risk_level = "low"

    # package with at least one alternative that has evidence
    alt = types.SimpleNamespace(evidence_basis=("evidence",))
    package = types.SimpleNamespace(alternatives=(alt,), requires_approval=False, selected_alternative="")

    res = gate.evaluate(evaluation=Eval(), package=package)
    assert res.passed is False
    assert hasattr(res, "rejection")
    assert res.rejection.gate_check in ("confidence", "evidence", "approval")


def test_runtime_integration_smoke():
    pe = OperationalPolicyEngine()
    audit = GuardianAudit()
    state_holder = GuardianStateHolder()
    gate = DecisionGate(pe)
    dashboard = GuardianDashboardService(None, gate, pe, state_holder, audit)
    integ = GuardianRuntimeIntegration(None, gate, pe, audit, state_holder, dashboard)

    out = integ.run()  # all None inputs
    assert out is not None
    assert isinstance(out.started_at, str)
    assert out.success is False
