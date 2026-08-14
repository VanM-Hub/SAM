"""M14-005/006 tests — AutomaticEscalation + AutonomousRecoveryLoop.

Fokus:
  - escalate saat authority/evidence tak cukup.
  - escalate saat verification gagal.
  - success=True TANPA independent verification DILARANG (fail honest).
  - recovery COMPLETED HANYA setelah verify ok.
  - tanpa execute_fn/verify_fn canonical -> FAILED (bukan sukses palsu).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


from sam.autonomy.models import AutonomyLevel
from sam.delegated_authority.authority import DelegationGrant, AuthorityVerdict
from sam.delegated_authority.escalation import AutomaticEscalation
from sam.delegated_authority.recovery import AutonomousRecoveryLoop, RecoveryPhase
from sam.execution_runtime.execution_request import ExecutionRequest


def _grant(level=AutonomyLevel.AUTONOMOUS, caps=("protect",), human=False):
    return DelegationGrant(
        ward_id="ward-1", owner_id="owner-1", autonomy_level=level,
        allowed_mutations=caps, requires_human_approval=human,
    )


def _req(operation="protect"):
    return ExecutionRequest(
        execution_id="exec-r1", provider_id="prov", operation=operation,
        mode="execute", approved=False, payload={"ward_id": "ward-1"},
    )


def _ok_fn():
    def fn(req):
        return {"ok": True, "result": "executed"}
    return fn


def _verify_ok():
    def fn(req):
        return {"ok": True, "verified": "independent-check-passed"}
    return fn


def _verify_fail():
    def fn(req):
        return {"ok": False, "error": "probe mismatch"}
    return fn


# ---------------- M14-005 AutomaticEscalation ----------------

class TestAutomaticEscalation:
    async def test_escalate_then_resolve_approve(self):
        e = AutomaticEscalation()
        req = await e.escalate_for(
            ward_id="ward-1", capability="protect", reason="evidence insufficient",
            verdict=AuthorityVerdict.ESCALATE, context={"plan": {"x": 1}},
        )
        assert req.status == "PENDING"
        pending = await e.pending()
        assert any(r.id == req.id for r in pending)

        out = await e.resolve(req.id, "approve", note="ok proceed")
        assert out.decided is True
        assert out.approve is True
        assert out.reject is False

    async def test_should_escalate_flags(self):
        from sam.delegated_authority.authority import AutonomousAuthority
        esc_auth = AutonomousAuthority(
            authority_id="a", ward_id="w", capability="c",
            verdict=AuthorityVerdict.ESCALATE,
        )
        block_auth = AutonomousAuthority(
            authority_id="b", ward_id="w", capability="c",
            verdict=AuthorityVerdict.BLOCKED,
        )
        assert AutomaticEscalation.should_escalate(esc_auth) is True
        assert AutomaticEscalation.should_escalate(block_auth) is True


# ---------------- M14-006 AutonomousRecoveryLoop ----------------

class TestAutonomousRecoveryLoop:
    async def test_completed_only_after_independent_verification(self):
        loop = AutonomousRecoveryLoop()
        learn_log = []
        out = await loop.run(
            request=_req(), grant=_grant(), risk=0.1, risk_label="low",
            evidence_refs=("ev-1",),
            execute_fn=_ok_fn(), verify_fn=_verify_ok(),
            learn_fn=lambda d: learn_log.append(d),
        )
        assert out.phase == RecoveryPhase.COMPLETED
        assert out.ok is True
        assert out.verification and out.verification.get("ok") is True
        assert len(learn_log) == 1

    async def test_verification_failure_never_success_explicitly(self):
        loop = AutonomousRecoveryLoop()
        out = await loop.run(
            request=_req(), grant=_grant(), risk=0.1, evidence_refs=("ev-1",),
            execute_fn=_ok_fn(), verify_fn=_verify_fail(),
        )
        # TIDAK success=True tanpa independent verification
        assert out.ok is False
        assert out.phase in (RecoveryPhase.FAILED, RecoveryPhase.ESCALATED,
                             RecoveryPhase.ROLLED_BACK)

    async def test_without_canonical_exec_fn_no_fake_success(self):
        loop = AutonomousRecoveryLoop()
        out = await loop.run(
            request=_req(), grant=_grant(), risk=0.1, evidence_refs=("ev-1",),
            execute_fn=None, verify_fn=None,
        )
        assert out.ok is False
        assert out.phase == RecoveryPhase.FAILED
        assert "no fake success" in out.reason

    async def test_no_grant_escalates_no_execution(self):
        loop = AutonomousRecoveryLoop()
        out = await loop.run(
            request=_req(), grant=None,
            evidence_refs=("ev-1",),
            execute_fn=_ok_fn(), verify_fn=_verify_ok(),
        )
        assert out.ok is False
        assert out.phase == RecoveryPhase.ESCALATED
        assert out.execution_result is None

    async def test_human_required_escalates(self):
        loop = AutonomousRecoveryLoop()
        out = await loop.run(
            request=_req(), grant=_grant(human=True),
            evidence_refs=("ev-1",),
            execute_fn=_ok_fn(), verify_fn=_verify_ok(),
        )
        assert out.ok is False
        assert out.phase == RecoveryPhase.ESCALATED
