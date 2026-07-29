"""
OP-344 — Guardian Decision Explanation

Bangun penjelasan manusia (rule-based, no LLM):
  Why approved / Why rejected
  Evidence summary
  Risks identified
  Policy status
  Recommendation
  Next actions

Immutable DTO. Synchronous only.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ExplanationSection:
    """Satu section dalam explanation."""
    title: str
    content: Tuple[str, ...] = field(default_factory=tuple)
    level: str = "info"  # info, warning, critical, success

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "content": list(self.content),
            "level": self.level,
        }


@dataclass(frozen=True)
class GovernanceExplanation:
    """Penjelasan lengkap governance decision."""
    explanation_id: str
    decision: str  # approved / rejected / deferred / escalated
    summary: str = ""
    sections: Tuple[ExplanationSection, ...] = field(default_factory=tuple)
    next_actions: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def section_count(self) -> int:
        return len(self.sections)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "decision": self.decision,
            "summary": self.summary,
            "sections": [s.title for s in self.sections],
            "next_actions": list(self.next_actions),
        }


class GuardianDecisionExplanation:
    """Pembangun penjelasan governance. Rule-based. No LLM."""

    def __init__(self) -> None:
        self._build_count = 0

    @property
    def build_count(self) -> int:
        return self._build_count

    def build(
        self,
        governance_status: str = "approved",
        governance_score: float = 1.0,
        policy_passed: bool = True,
        policy_violations: int = 0,
        health_status: str = "healthy",
        health_score: float = 1.0,
        decision_approved: bool = True,
        decision_confidence: float = 1.0,
        approval_complete: bool = True,
        approval_granted: int = 0,
        approval_required: int = 0,
        recommendation_support: bool = True,
        recommendation_risk: str = "low",
        risk_level: str = "none",
        risk_score: float = 0.0,
        risk_dimensions: Optional[Tuple[str, ...]] = None,
        readiness_level: str = "ready",
        readiness_score: float = 1.0,
        readiness_blocking: Optional[Tuple[str, ...]] = None,
        evidence_items: Optional[Tuple[str, ...]] = None,
        explanation_id: Optional[str] = None,
        **kwargs: Any,
    ) -> GovernanceExplanation:
        """Bangun penjelasan governance decision.

        Returns:
            GovernanceExplanation immutable.
        """
        import uuid
        eid = explanation_id or f"gex-{uuid.uuid4().hex[:8]}"
        self._build_count += 1
        sections: List[ExplanationSection] = []
        next_actions: List[str] = []

        # ── Summary ──
        if governance_status == "approved":
            summary = "✅ Governance APPROVED — operasi siap dijalankan"
        elif governance_status == "rejected":
            summary = "❌ Governance REJECTED — operasi tidak dapat dijalankan"
        elif governance_status == "deferred":
            summary = "⏳ Governance DEFERRED — menunggu kondisi terpenuhi"
        else:
            summary = "⚠️ Governance ESCALATED — perlu intervensi manual"

        # ── Section: Why ──
        why_lines: list = []
        if governance_status == "approved":
            why_lines.append(f"Semua stage governance lolos (score: {governance_score:.2f})")
        elif governance_status == "rejected":
            if not policy_passed:
                why_lines.append("Policy violation: policy tidak lolos")
            if not decision_approved:
                why_lines.append("Decision tidak mendukung eksekusi")
        elif governance_status == "deferred":
            if not approval_complete:
                missing = max(0, approval_required - approval_granted)
                why_lines.append(f"Approval belum lengkap: kurang {missing}")
            if health_status == "critical":
                why_lines.append("System health kritis")
        elif governance_status == "escalated":
            why_lines.append("Rekomendasi memerlukan eskalasi manual")

        sections.append(ExplanationSection(
            title="Keputusan Governance",
            content=tuple(why_lines),
            level="success" if governance_status == "approved" else "critical",
        ))

        # ── Section: Evidence ──
        ev_lines: list = []
        if evidence_items:
            ev_lines.extend(evidence_items)
        if decision_approved:
            ev_lines.append(f"Decision confidence: {decision_confidence:.2f}")
        if approval_complete:
            ev_lines.append(f"Approval: {approval_granted}/{approval_required} granted")
        else:
            ev_lines.append(f"Approval: {approval_granted}/{approval_required} — incomplete")

        sections.append(ExplanationSection(
            title="Evidence",
            content=tuple(ev_lines),
            level="info",
        ))

        # ── Section: Risks ──
        risk_lines: list = []
        risk_lines.append(f"Risk level: {risk_level} (score: {risk_score:.2f})")
        if risk_dimensions:
            for dim in risk_dimensions:
                risk_lines.append(f"  - {dim}")
        if recommendation_risk != "low" and recommendation_risk:
            risk_lines.append(f"Recommendation risk: {recommendation_risk}")

        risk_level_tag = "success" if risk_level in ("none", "low") else (
            "warning" if risk_level == "medium" else "critical")
        sections.append(ExplanationSection(
            title="Risiko Teridentifikasi",
            content=tuple(risk_lines),
            level=risk_level_tag,
        ))

        # ── Section: Policy ──
        pol_lines: list = []
        if policy_passed:
            pol_lines.append("✅ Semua policy compliance check lolos")
        else:
            pol_lines.append(f"❌ {policy_violations} policy violation(s) terdeteksi")
            pol_lines.append("Policy violation menghalangi eksekusi")
        sections.append(ExplanationSection(
            title="Policy Compliance",
            content=tuple(pol_lines),
            level="success" if policy_passed else "critical",
        ))

        # ── Section: Recommendation ──
        rec_lines: list = []
        if recommendation_support:
            rec_lines.append("✅ Recommendation mendukung eksekusi")
        else:
            rec_lines.append("⚠️ Recommendation tidak mendukung eksekusi")
        rec_lines.append(f"Risk: {recommendation_risk}")
        sections.append(ExplanationSection(
            title="Recommendation",
            content=tuple(rec_lines),
            level="success" if recommendation_support else "warning",
        ))

        # ── Next Actions ──
        if governance_status == "approved":
            next_actions.append("✅ Operasi siap dijalankan")
            if risk_level not in ("none", "low"):
                next_actions.append("⚠️ Waspada risk level — monitor selama eksekusi")
        elif governance_status == "rejected":
            if not policy_passed:
                next_actions.append("🔧 Perbaiki policy violations sebelum resubmit")
            if not decision_approved:
                next_actions.append("🔧 Perkuat decision dengan evidence tambahan")
        elif governance_status == "deferred":
            if not approval_complete:
                missing = max(0, approval_required - approval_granted)
                next_actions.append(f"📋 Dapatkan {missing} approval yang kurang")
            if health_status == "critical":
                next_actions.append("🏥 Pulihkan system health sebelum resubmit")
        elif governance_status == "escalated":
            next_actions.append("👤 Eskalasi ke human operator untuk review manual")

        if readiness_blocking:
            for bdim in readiness_blocking:
                next_actions.append(f"🔧 Selesaikan blocking: {bdim}")

        # Tambahkan rekomendasi dari readiness
        if readiness_level != "ready":
            next_actions.append(f"⏳ Status readiness: {readiness_level} (score: {readiness_score:.2f})")

        return GovernanceExplanation(
            explanation_id=eid,
            decision=governance_status,
            summary=summary,
            sections=tuple(sections),
            next_actions=tuple(next_actions),
        )
