"""
OP-341 — Guardian Governance Engine

Pipeline evaluasi governance:
  Policy → Health → Decision → Approval → Recommendation → Final Result

Tidak ada side effect. Hanya evaluasi read-only.
Immutable DTOs. Synchronous only.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


# ── Enums ──

class GovernanceStatus(str, Enum):
    """Status governance final."""
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    ESCALATED = "escalated"


class GovernanceStage(str, Enum):
    """Stage governance yang dievaluasi."""
    POLICY = "policy"
    HEALTH = "health"
    DECISION = "decision"
    APPROVAL = "approval"
    RECOMMENDATION = "recommendation"


# ── DTOs ──

@dataclass(frozen=True)
class GovernanceEvidence:
    """Satu bukti yang mendukung keputusan governance."""
    stage: str
    key: str
    value: Any
    is_passing: bool
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "key": self.key,
            "value": self.value,
            "is_passing": self.is_passing,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class GovernanceDecision:
    """Keputusan governance pada satu stage."""
    stage: GovernanceStage
    status: GovernanceStatus
    score: float = 0.0
    evidence: Tuple[GovernanceEvidence, ...] = field(default_factory=tuple)
    reason: str = ""
    warnings: Tuple[str, ...] = field(default_factory=tuple)
    errors: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return self.status == GovernanceStatus.APPROVED

    @property
    def evidence_count(self) -> int:
        return len(self.evidence)

    @property
    def passing_evidence(self) -> List[GovernanceEvidence]:
        return [e for e in self.evidence if e.is_passing]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "status": self.status.value,
            "score": self.score,
            "passed": self.passed,
            "evidence_count": self.evidence_count,
            "reason": self.reason,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


@dataclass(frozen=True)
class GovernanceResult:
    """Hasil final governance pipeline."""
    governance_id: str
    overall_status: GovernanceStatus
    stages: Tuple[GovernanceDecision, ...] = field(default_factory=tuple)
    overall_score: float = 0.0
    summary: str = ""
    warnings: Tuple[str, ...] = field(default_factory=tuple)
    errors: Tuple[str, ...] = field(default_factory=tuple)
    evidence: Tuple[GovernanceEvidence, ...] = field(default_factory=tuple)

    @property
    def approved(self) -> bool:
        return self.overall_status == GovernanceStatus.APPROVED

    @property
    def stage_count(self) -> int:
        return len(self.stages)

    @property
    def failed_stages(self) -> List[str]:
        return [s.stage.value for s in self.stages if not s.passed]

    @property
    def stage_decisions(self) -> Dict[str, GovernanceDecision]:
        return {s.stage.value: s for s in self.stages}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "governance_id": self.governance_id,
            "overall_status": self.overall_status.value,
            "overall_score": self.overall_score,
            "approved": self.approved,
            "stage_count": self.stage_count,
            "failed_stages": self.failed_stages,
            "stages": [s.stage.value for s in self.stages],
            "summary": self.summary,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


# ── Engine ──

class GuardianGovernanceEngine:
    """Pipeline governance 5-stage: Policy → Health → Decision → Approval → Recommendation.

    Hanya evaluasi. Tidak ada side effect. Synchronous.
    """

    STAGES = ["policy", "health", "decision", "approval", "recommendation"]

    def __init__(self) -> None:
        self._evaluation_count = 0

    @property
    def evaluation_count(self) -> int:
        return self._evaluation_count

    def evaluate(
        self,
        policy_passed: bool = True,
        policy_violations: int = 0,
        health_status: str = "healthy",
        health_score: float = 1.0,
        decision_approved: bool = True,
        decision_confidence: float = 1.0,
        approval_complete: bool = True,
        approval_required: int = 0,
        approval_granted: int = 0,
        recommendation_support: bool = True,
        recommendation_risk: str = "low",
        recommendation_confidence: float = 1.0,
        governance_id: Optional[str] = None,
        **kwargs: Any,
    ) -> GovernanceResult:
        """Evaluasi governance pipeline 5-stage.

        Args:
            policy_passed: Apakah semua policy lolos.
            policy_violations: Jumlah pelanggaran policy.
            health_status: Status health engine (healthy/degraded/critical).
            health_score: Skor health engine (0.0 - 1.0).
            decision_approved: Apakah decision setuju.
            decision_confidence: Confidence decision (0.0 - 1.0).
            approval_complete: Apakah semua approval lengkap.
            approval_required: Berapa approval dibutuhkan.
            approval_granted: Berapa approval diberikan.
            recommendation_support: Apakah recommendation mendukung.
            recommendation_risk: Tingkat risk recommendation.
            recommendation_confidence: Confidence recommendation.
            governance_id: Opsional override ID.

        Returns:
            GovernanceResult immutable.
        """
        import uuid
        gid = governance_id or f"gov-{uuid.uuid4().hex[:8]}"
        self._evaluation_count += 1
        all_evidence: List[GovernanceEvidence] = []
        decisions: List[GovernanceDecision] = []
        global_warnings: List[str] = []
        global_errors: List[str] = []

        # ── Stage 1: Policy ──
        policy_evidence = [
            GovernanceEvidence("policy", "policy_passed", policy_passed, policy_passed,
                             "Semua policy compliance check"),
            GovernanceEvidence("policy", "policy_violations", policy_violations,
                             policy_violations == 0,
                             f"{policy_violations} violations found"),
        ]
        all_evidence.extend(policy_evidence)
        policy_ok = policy_passed and policy_violations == 0
        policy_warnings: list = []
        if policy_violations > 0:
            policy_warnings.append(f"{policy_violations} policy violation(s)")
        decisions.append(GovernanceDecision(
            stage=GovernanceStage.POLICY,
            status=GovernanceStatus.APPROVED if policy_ok else GovernanceStatus.REJECTED,
            score=1.0 if policy_ok else max(0.0, 1.0 - policy_violations * 0.2),
            evidence=tuple(policy_evidence),
            reason="All policies passed" if policy_ok else "Policy violations detected",
            warnings=tuple(policy_warnings),
        ))

        # ── Stage 2: Health ──
        health_evidence = [
            GovernanceEvidence("health", "health_status", health_status,
                             health_status in ("healthy", "degraded"),
                             f"Health status: {health_status}"),
            GovernanceEvidence("health", "health_score", health_score,
                             health_score >= 0.5,
                             f"Health score: {health_score:.2f}"),
        ]
        all_evidence.extend(health_evidence)
        health_ok = health_status != "critical" and health_score >= 0.5
        health_warnings: list = []
        if health_status == "degraded":
            health_warnings.append("System degraded")
        elif health_status == "critical":
            health_warnings.append("System critical — high risk")
        decisions.append(GovernanceDecision(
            stage=GovernanceStage.HEALTH,
            status=GovernanceStatus.APPROVED if health_ok else GovernanceStatus.DEFERRED,
            score=health_score,
            evidence=tuple(health_evidence),
            reason="System healthy" if health_ok else f"System {health_status}",
            warnings=tuple(health_warnings),
        ))

        # ── Stage 3: Decision ──
        decision_evidence = [
            GovernanceEvidence("decision", "decision_approved", decision_approved,
                             decision_approved, "Decision approval status"),
            GovernanceEvidence("decision", "decision_confidence", decision_confidence,
                             decision_confidence >= 0.7,
                             f"Confidence: {decision_confidence:.2f}"),
        ]
        all_evidence.extend(decision_evidence)
        decision_ok = decision_approved and decision_confidence >= 0.7
        decisions.append(GovernanceDecision(
            stage=GovernanceStage.DECISION,
            status=GovernanceStatus.APPROVED if decision_ok else GovernanceStatus.REJECTED,
            score=decision_confidence,
            evidence=tuple(decision_evidence),
            reason="Decision supports execution" if decision_ok else "Decision does not support",
        ))

        # ── Stage 4: Approval ──
        approval_evidence = [
            GovernanceEvidence("approval", "approval_complete", approval_complete,
                             approval_complete, "Approval completeness"),
            GovernanceEvidence("approval", "approval_required", approval_required,
                             approval_granted >= approval_required,
                             f"{approval_granted}/{approval_required} granted"),
        ]
        all_evidence.extend(approval_evidence)
        approval_ok = approval_complete and approval_granted >= approval_required
        approval_warnings: list = []
        if approval_required > 0 and approval_granted < approval_required:
            approval_warnings.append(
                f"Missing {approval_required - approval_granted} approval(s)")
        decisions.append(GovernanceDecision(
            stage=GovernanceStage.APPROVAL,
            status=GovernanceStatus.APPROVED if approval_ok else GovernanceStatus.DEFERRED,
            evidence=tuple(approval_evidence),
            reason="Approval complete" if approval_ok else "Approval incomplete",
            warnings=tuple(approval_warnings),
        ))

        # ── Stage 5: Recommendation ──
        rec_evidence = [
            GovernanceEvidence("recommendation", "recommendation_support",
                             recommendation_support, recommendation_support,
                             "Recommendation support"),
            GovernanceEvidence("recommendation", "recommendation_risk",
                             recommendation_risk, recommendation_risk == "low",
                             f"Risk level: {recommendation_risk}"),
        ]
        all_evidence.extend(rec_evidence)
        rec_ok = recommendation_support and recommendation_risk == "low"
        rec_warnings: list = []
        if recommendation_risk == "medium":
            rec_warnings.append("Medium risk — proceed with caution")
        elif recommendation_risk == "high":
            rec_warnings.append("High risk — escalation recommended")
        decisions.append(GovernanceDecision(
            stage=GovernanceStage.RECOMMENDATION,
            status=GovernanceStatus.APPROVED if rec_ok else (
                GovernanceStatus.ESCALATED if recommendation_risk == "high"
                else GovernanceStatus.DEFERRED),
            score=recommendation_confidence,
            evidence=tuple(rec_evidence),
            reason="Recommendation supports" if rec_ok else f"Risk level: {recommendation_risk}",
            warnings=tuple(rec_warnings),
        ))

        # ── Summary ──
        passed_stages = [d for d in decisions if d.passed]
        overall_score = sum(d.score for d in decisions) / len(decisions) if decisions else 0.0

        if all(d.passed for d in decisions):
            overall_status = GovernanceStatus.APPROVED
            summary = "Governance approved — all stages passed"
        elif any(d.status == GovernanceStatus.REJECTED for d in decisions):
            overall_status = GovernanceStatus.REJECTED
            failed = [d.stage.value for d in decisions if not d.passed]
            summary = f"Governance rejected — failed: {', '.join(failed)}"
        elif any(d.status == GovernanceStatus.ESCALATED for d in decisions):
            overall_status = GovernanceStatus.ESCALATED
            summary = "Governance escalated — requires human intervention"
        else:
            overall_status = GovernanceStatus.DEFERRED
            deferred = [d.stage.value for d in decisions if not d.passed]
            summary = f"Governance deferred — pending: {', '.join(deferred)}"

        # Collect global warnings
        for d in decisions:
            global_warnings.extend(d.warnings)
        global_warnings.extend(approval_warnings)
        global_warnings.extend(rec_warnings)

        return GovernanceResult(
            governance_id=gid,
            overall_status=overall_status,
            stages=tuple(decisions),
            overall_score=overall_score,
            summary=summary,
            warnings=tuple(global_warnings),
            errors=tuple(global_errors),
            evidence=tuple(all_evidence),
        )
