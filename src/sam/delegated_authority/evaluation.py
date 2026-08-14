"""M14-003 AuthorityEvaluation — evaluasi authority (deterministik).

Urutan evaluasi per tindakan (FLOW M14):
    Policy -> Risk -> Evidence -> Autonomous Authority -> Guardrails

Komponen yang DIPAKAI ULANG (bukan dibuat ulang):
    - AutonomyLevel.can_execute(risk)      (autonomy/models.py)
    - Guardrails.evaluate(action)          (autonomy/guardrails.py)
    - SelfAssessment.assess_before(action) (autonomy/assessment.py)
    - WardGovernanceBoundary (M13)         (ward/governance/boundary.py)
    - Entrustment (M13)                    (ward/entrustment/models.py)

Evaluator ini TIDAK mengeksekusi apa pun dan TIDAK mengubah authority.
Ia hanya MENILAI: apakah delegated authority mengizinkan auto-approve.
Keputusan eksekusi tetap milik ApprovalGate + canonical executor.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from sam.autonomy.assessment import SelfAssessment, AssessmentResult
from sam.autonomy.guardrails import (
    Guardrails, DECISION_ALLOW, DECISION_WARN, DECISION_BLOCK,
)
from sam.delegated_authority.authority import (
    AutonomousAuthority, AuthoritySource, AuthorityVerdict, DelegationGrant,
)


class AuthorityEvaluation:
    """Mengevaluasi delegated authority atas satu tindakan mutation."""

    def __init__(
        self,
        assessment: Optional[SelfAssessment] = None,
        guardrails: Optional[Guardrails] = None,
    ) -> None:
        self._assessment = assessment or SelfAssessment()
        self._guardrails = guardrails or Guardrails()

    # --- public API ---

    async def evaluate(
        self,
        *,
        ward_id: str,
        capability: str,
        grant: Optional[DelegationGrant],
        risk: float = 0.0,
        risk_label: str = "low",
        evidence_refs: tuple = (),
        action_context: Optional[Dict[str, Any]] = None,
    ) -> AutonomousAuthority:
        """Evaluasi authority untuk satu mutation.

        Fail-closed: tanpa grant / entrustment non-aktif -> NO_AUTHORITY.
        Guardrail blok  -> BLOCKED.
        Evidence/assess kurang -> ESCALATE.
        Grant setuju   -> AUTO_APPROVE.
        """
        # 1) Entrustment wajib (fail-closed M13-010).
        if grant is None:
            return AutonomousAuthority(
                authority_id=AutonomousAuthority.new_id(),
                ward_id=ward_id, capability=capability,
                source=AuthoritySource.NONE,
                verdict=AuthorityVerdict.NO_AUTHORITY,
                reason="no active entrustment - fail closed",
            )

        action = dict(action_context or {})
        action.setdefault("capability", capability)
        action.setdefault("ward_id", ward_id)
        action.setdefault("risk", risk)

        # 2) Guardrails dulu (block/escalate menang atas auto-approve).
        guardrail = await self._guardrails.evaluate(action)
        if guardrail.decision == DECISION_BLOCK:
            return AutonomousAuthority(
                authority_id=AutonomousAuthority.new_id(),
                ward_id=ward_id, capability=capability,
                source=AuthoritySource.ENTRUSTMENT,
                verdict=AuthorityVerdict.BLOCKED,
                grant=grant.as_dict(),
                reason=f"guardrail blocked: {guardrail.details}",
                evidence_refs=evidence_refs,
            )
        auto_from_guardrail = guardrail.decision in (DECISION_WARN, DECISION_ALLOW)

        # 3) Self-assessment (confidence). Assessment TIDAK menaikkan authority,
        #    hanya memberi sinyal: tidak boleh auto-approve bila terlalu ragu.
        assess = await self._assessment.assess_before(action)
        evidence_ok = self._sufficient_evidence(evidence_refs, assess)

        # 4) Keputusan authority (deterministik, dari mandat owner).
        auto_allowed = grant.allows_auto_approve(capability, risk_label)

        auto_ok = (
            auto_allowed and auto_from_guardrail and evidence_ok
        )

        if auto_ok:
            return AutonomousAuthority(
                authority_id=AutonomousAuthority.new_id(),
                ward_id=ward_id, capability=capability,
                source=AuthoritySource.ENTRUSTMENT,
                verdict=AuthorityVerdict.AUTO_APPROVE,
                grant=grant.as_dict(),
                reason=f"delegated authority (level={grant.autonomy_level.value}, risk={risk_label}) "
                       f"+ guardrail ok + evidence sufficient",
                evidence_refs=evidence_refs,
            )

        # Auto-approve tak cukup -> ESCALATE (bukan BLOCKED) selama ada grant
        # & bukan pelanggaran keras.
        escalate_reasons = []
        if not evidence_ok:
            escalate_reasons.append("evidence insufficient")
        if not auto_from_guardrail:
            escalate_reasons.append("guardrail warn")
        if not auto_allowed and not grant.requires_human_approval:
            escalate_reasons.append("autonomy level / capability not auto-granted")
        if grant.requires_human_approval:
            escalate_reasons.append("policy requires human approval")
        if not escalate_reasons:
            escalate_reasons.append("authority insufficient")

        return AutonomousAuthority(
            authority_id=AutonomousAuthority.new_id(),
            ward_id=ward_id, capability=capability,
            source=AuthoritySource.ENTRUSTMENT,
            verdict=AuthorityVerdict.ESCALATE,
            grant=grant.as_dict(),
            reason="; ".join(escalate_reasons),
            evidence_refs=evidence_refs,
        )

    # --- helpers ---

    @staticmethod
    def _sufficient_evidence(
        evidence_refs: tuple, assess: AssessmentResult
    ) -> bool:
        """Evidence dianggap cukup bila ada acuan + confidence tidak rendah."""
        if not evidence_refs:
            return False
        if assess.confidence < 30.0:
            return False
        return True
