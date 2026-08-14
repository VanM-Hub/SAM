"""M14 foundation tests — AutonomousAuthority, AuthorityEvaluation,
DelegatedApprovalProvider, ScopedAutonomy (001-004).

Focus:
  - delegation adalah dari OWNER, bukan self-grant.
  - authority tidak pernah naik lewat learning/confidence.
  - approval tetap SATU (ApprovalGate) — provider tidak mengeksekusi.
  - fail-closed: tanpa entrustment / capability tak diizinkan -> tidak auto-approve.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

import asyncio
import pytest

from sam.autonomy.models import AutonomyLevel
from sam.delegated_authority.authority import (
    DelegationGrant, AutonomousAuthority, AuthorityVerdict, AuthoritySource,
)
from sam.delegated_authority.evaluation import AuthorityEvaluation
from sam.delegated_authority.provider import DelegatedApprovalProvider
from sam.delegated_authority.scope import ScopedAutonomy
from sam.execution_runtime.execution_request import ExecutionRequest


def _grant(level=AutonomyLevel.AUTONOMOUS, caps=("protect",), human=False):
    return DelegationGrant(
        ward_id="ward-1", owner_id="owner-1",
        autonomy_level=level, allowed_mutations=caps,
        requires_human_approval=human,
    )


def _req(execution_id="exec-1", operation="protect"):
    return ExecutionRequest(
        execution_id=execution_id, provider_id="prov",
        operation=operation, mode="execute", approved=False,
    )


# ---------------- M14-001 AutonomousAuthority (model) ----------------

class TestDelegationGrant:
    def test_auto_approve_allowed_only_when_capability_granted(self):
        g = _grant()
        assert g.allows_auto_approve("protect", "low") is True
        assert g.allows_auto_approve("delete", "low") is False  # bukan di allowed

    def test_human_approval_required_never_auto_approve(self):
        g = _grant(human=True)
        assert g.allows_auto_approve("protect", "low") is False

    def test_autonomy_level_gates_auto_approve(self):
        # OBSERVE tidak pernah eksekusi -> tidak auto-approve
        g = _grant(level=AutonomyLevel.OBSERVE)
        assert g.allows_auto_approve("protect", "low") is False

    def test_grant_is_owner_sourced(self):
        g = _grant()
        d = g.as_dict()
        assert d["owner_id"] == "owner-1"
        assert d["autonomy_level"] == "autonomous"


class TestAutonomousAuthority:
    def test_verdict_helpers(self):
        a = AutonomousAuthority(
            authority_id="aut-1", ward_id="ward-1", capability="protect",
            source=AuthoritySource.ENTRUSTMENT,
            verdict=AuthorityVerdict.AUTO_APPROVE,
        )
        assert a.auto_approve_allowed is True
        assert a.escalate is False

    def test_deterministic_id_generated_when_empty(self):
        a = AutonomousAuthority(authority_id="", ward_id="w", capability="c")
        assert a.authority_id.startswith("aut_")


# ---------------- M14-003 AuthorityEvaluation ----------------

class TestAuthorityEvaluation:
    async def test_no_grant_fail_closed(self):
        ev = AuthorityEvaluation()
        a = await ev.evaluate(ward_id="ward-1", capability="protect", grant=None,
                              evidence_refs=("ev-1",))
        assert a.verdict == AuthorityVerdict.NO_AUTHORITY
        assert a.auto_approve_allowed is False

    async def test_auto_approve_when_evidence_and_grant_ok(self):
        ev = AuthorityEvaluation()
        a = await ev.evaluate(ward_id="ward-1", capability="protect", grant=_grant(),
                              risk=0.1, risk_label="low", evidence_refs=("ev-1",))
        assert a.verdict == AuthorityVerdict.AUTO_APPROVE

    async def test_escalate_when_evidence_missing(self):
        ev = AuthorityEvaluation()
        a = await ev.evaluate(ward_id="ward-1", capability="protect", grant=_grant(),
                              risk=0.1, evidence_refs=())
        assert a.verdict == AuthorityVerdict.ESCALATE

    async def test_escalate_when_human_required(self):
        ev = AuthorityEvaluation()
        a = await ev.evaluate(ward_id="ward-1", capability="protect", grant=_grant(human=True),
                              risk=0.1, evidence_refs=("ev-1",))
        assert a.verdict == AuthorityVerdict.ESCALATE


# ---------------- M14-002 DelegatedApprovalProvider ----------------

class TestDelegatedApprovalProvider:
    async def test_provider_approves_execution_when_verdict_auto(self):
        p = DelegatedApprovalProvider()
        req = _req()
        out = await p.approve_for(
            req, grant=_grant(), risk=0.1, risk_label="low",
            evidence_refs=("ev-1",),
            action_context={"ward_id": "ward-1"},
        )
        assert out.approved is True
        assert out.source == "delegated"
        assert out.approver == "delegated:ward-1"

    async def test_provider_never_auto_approves_without_grant(self):
        p = DelegatedApprovalProvider()
        out = await p.approve_for(
            _req(), grant=None, evidence_refs=("ev-1",),
            action_context={"ward_id": "ward-1"},
        )
        assert out.approved is False

    async def test_provider_does_not_auto_approve_human_required(self):
        p = DelegatedApprovalProvider()
        out = await p.approve_for(
            _req(), grant=_grant(human=True), evidence_refs=("ev-1",),
            action_context={"ward_id": "ward-1"},
        )
        assert out.approved is False
        assert out.verdict == "escalate"

    async def test_full_request_carries_approval_but_still_gate(self):
        p = DelegatedApprovalProvider()
        req = _req()
        out = await p.approve_for(
            req, grant=_grant(), risk=0.1, evidence_refs=("ev-1",),
            action_context={"ward_id": "ward-1"},
        )
        full = p.full_request(req, out)
        # canonical gate masih mengharuskan approved
        assert p.may_execute(full) is True
        assert full.approved is True
        assert full.approver == "delegated:ward-1"


# ---------------- M14-004 ScopedAutonomy ----------------

class TestScopedAutonomy:
    def test_scope_lower_bound_and_no_self_raise(self):
        s = ScopedAutonomy()
        s.bind("ward-1", "protect", AutonomyLevel.AUTONOMOUS)
        assert s.current("ward-1", "protect") == AutonomyLevel.AUTONOMOUS
        assert s.upper("ward-1", "protect") == AutonomyLevel.AUTONOMOUS
        # kenaikan di atas upper dilarang (self-grant dilarang)
        assert s.grant_allows("ward-1", "protect", AutonomyLevel.AUTONOMOUS, "low") is True
        # capability tak di-bind -> tidak diizinkan
        assert s.grant_allows("ward-1", "delete", AutonomyLevel.AUTONOMOUS, "low") is False

    def test_degrade_only(self):
        s = ScopedAutonomy()
        s.bind("ward-1", "protect", AutonomyLevel.SUPERVISE)
        new = s.degrade("ward-1", "protect", reason="safety")
        assert new == AutonomyLevel.ASSIST
        assert s.current("ward-1", "protect") == AutonomyLevel.ASSIST
        assert s.history()[0]["from"] == "supervise"
        assert s.history()[0]["to"] == "assist"
