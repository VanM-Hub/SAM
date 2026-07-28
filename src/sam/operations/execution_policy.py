"""
Decision Execution Policy — memetakan risk level ke execution path.

Untuk setiap risk level:
  - approval: auto/once/always
  - verification: auto/evidence
  - audit: log/file/detailed
  - rollback: none/optional/required

Policy ini dijalankan OTOMATIS oleh Conversation.
Tidak bisa di-skip.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

from .risk_classification import RiskLevel, CAPABILITY_RISK, get_risk_rule


class ExecutionDecision(str, Enum):
    """Keputusan apakah plan boleh dieksekusi."""
    APPROVED = "approved"           # Boleh eksekusi
    NEEDS_APPROVAL = "needs_approval"  # Butuh approval manusia
    BLOCKED = "blocked"             # Diblokir (HIGH/CRITICAL tanpa approval)
    REJECTED = "rejected"           # Ditolak oleh policy
    DEFERRED = "deferred"           # Ditunda (butuh info tambahan)
    SIMULATED = "simulated"         # Mode simulasi


@dataclass
class ExecutionPolicyDecision:
    """Keputusan policy untuk satu execution.

    Dibuat oleh ExecutionPolicy sebelum execution.
    """
    action_id: str
    action_title: str
    category: str = ""
    risk_level: RiskLevel = RiskLevel.MEDIUM

    decision: ExecutionDecision = ExecutionDecision.NEEDS_APPROVAL

    # Rules applied
    approval_type: str = "always"
    verification_type: str = "evidence"
    rollout_type: str = "none"
    audit_type: str = "log"

    # Human overrides
    can_auto_execute: bool = False
    requires_human: bool = True
    approval_required: bool = True
    escalation_available: bool = False

    # Evidence
    reason: str = ""
    blocking_reason: str = ""
    required_evidence: List[str] = field(default_factory=list)

    def to_text(self) -> str:
        return "{status}: {title} [{risk}] — approval={ap}, verify={vf}, rollback={rb}".format(
            status=self.decision.value.upper(),
            title=self.action_title,
            risk=self.risk_level.value,
            ap=self.approval_type,
            vf=self.verification_type,
            rb=self.rollout_type,
        )

    def to_dict(self) -> dict:
        return {
            "action_id": self.action_id,
            "action_title": self.action_title,
            "category": self.category,
            "risk_level": self.risk_level.value,
            "decision": self.decision.value,
            "approval_type": self.approval_type,
            "verification_type": self.verification_type,
            "rollout_type": self.rollout_type,
            "audit_type": self.audit_type,
            "can_auto_execute": self.can_auto_execute,
            "requires_human": self.requires_human,
            "approval_required": self.approval_required,
            "reason": self.reason,
            "blocking_reason": self.blocking_reason,
        }


class ExecutionPolicy:
    """Policy yang memetakan risk level → execution path.

    Method utama: evaluate(actions) -> List[ExecutionPolicyDecision]
    Method akses: can_execute(), requires_approval()

    Policy bersifat read-only — tidak mengubah state.
    Conversation adalah satu-satunya pembaca.
    """

    def evaluate(self, plan, approved_items: List[str] = None,
                 simulation_mode: bool = False) -> List[ExecutionPolicyDecision]:
        """Evaluasi semua action dalam plan.

        Args:
            plan: ExecutionPlan
            approved_items: List[approval_id] yang sudah di-approve
            simulation_mode: Jika True, semua action SIMULATED

        Returns:
            List[ExecutionPolicyDecision]
        """
        approved_items = approved_items or []
        decisions = []

        for i, action in enumerate(plan.actions):
            category = getattr(action, 'category', 'general')
            title = getattr(action, 'title', 'Unknown')
            action_id = getattr(action, 'action_id', 'act-{:03d}'.format(i))

            risk = self._classify_by_category(category)
            dec = self._evaluate_one(
                action_id=action_id,
                title=title,
                category=category,
                risk_level=risk,
                approved_items=approved_items,
                simulation_mode=simulation_mode,
            )
            decisions.append(dec)

        return decisions

    def _evaluate_one(self, action_id: str, title: str, category: str,
                      risk_level: RiskLevel,
                      approved_items: List[str],
                      simulation_mode: bool) -> ExecutionPolicyDecision:
        """Evaluasi satu action."""
        rule = get_risk_rule(risk_level)

        dec = ExecutionPolicyDecision(
            action_id=action_id,
            action_title=title,
            category=category,
            risk_level=risk_level,
            approval_type=rule.approval,
            verification_type=rule.verification,
            rollout_type=rule.rollback,
            audit_type=rule.audit,
            can_auto_execute=rule.can_auto_execute,
            requires_human=rule.requires_human,
        )

        if simulation_mode:
            dec.decision = ExecutionDecision.SIMULATED
            dec.reason = "Simulation mode — semua action SIMULATED"
            dec.approval_required = False
            return dec

        # Auto-execute (SAFE, LOW)
        if rule.can_auto_execute:
            dec.decision = ExecutionDecision.APPROVED
            dec.approval_required = False
            dec.reason = "Auto-approved: risk level = {}".format(risk_level.value)
            return dec

        # Needs approval (MEDIUM, HIGH, CRITICAL)
        if rule.approval == "always":
            dec.approval_required = True
            dec.reason = "Always approval required: risk level = {}".format(risk_level.value)

            # Check if already approved
            if any(aid in action_id for aid in approved_items) or action_id in approved_items:
                dec.decision = ExecutionDecision.APPROVED
                dec.reason = "Approved by prior approval"
            else:
                dec.decision = ExecutionDecision.NEEDS_APPROVAL
                dec.blocking_reason = "Butuh approval manusia (risk={})".format(risk_level.value)
                dec.required_evidence = [
                    "Manusia harus menyetujui action: {}".format(title),
                ]

            return dec

        # Once approval
        if rule.approval == "once":
            dec.approval_required = True
            dec.reason = "Once approval: risk level = {}".format(risk_level.value)
            dec.decision = ExecutionDecision.APPROVED  # Once = approved asumsi (belum ada tracking)
            return dec

        return dec

    def _classify_by_category(self, category: str) -> RiskLevel:
        """Mapping category → default risk."""
        cat_risk = {
            "filesystem": RiskLevel.MEDIUM,
            "command": RiskLevel.HIGH,
            "system": RiskLevel.MEDIUM,
            "process": RiskLevel.HIGH,
            "workspace": RiskLevel.LOW,
            "network": RiskLevel.LOW,
            "database": RiskLevel.CRITICAL,
            "general": RiskLevel.MEDIUM,
        }
        return cat_risk.get(category, RiskLevel.MEDIUM)

    @staticmethod
    def can_execute(decisions: List[ExecutionPolicyDecision]) -> bool:
        """Apakah semua action bisa dieksekusi?"""
        if not decisions:
            return False
        return all(
            d.decision in (ExecutionDecision.APPROVED, ExecutionDecision.SIMULATED)
            for d in decisions
        )

    @staticmethod
    def requires_approval(decisions: List[ExecutionPolicyDecision]) -> bool:
        """Apakah ada action yang butuh approval?"""
        return any(d.decision == ExecutionDecision.NEEDS_APPROVAL for d in decisions)
